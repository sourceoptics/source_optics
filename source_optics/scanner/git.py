# Copyright 2018 SourceOptics Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import subprocess
import getpass
import re
import datetime
import traceback

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.conf import settings
from .. models import *
from .. create import Creator
from django.db import transaction
from . import commands

GIT_TYPES = ["https://", "http://"]

# The parser will use regex to grab the fields from the
# github pretty print. Fields with (?P<name>) are the
# capture groups used to turn matching areas of the pretty
# string into entries in a dictionary. The parser wants the
# entire string in one line (it reads line by line)
#
# The delimitor (DEL) will separate each field to parse
DEL = '&DEL&'

# Fields recorded (in order)
# commit hash %H
# author_name %an
# author_date %ad
# commit_date %cd
# author_email %ae
# subject %f
PRETTY_STRING = ('\'' + DEL + '%H' + DEL
        + '%an' + DEL
        + '%ad' + DEL
        + '%cd' + DEL
        + '%ae' + DEL
        + '%f' + DEL
        + '\'')

# our regex to match the string. must be in same order as fields in PRETTY_STRING
# to add fields in the future, add a line to this query:
# PARSER_RE_STRING = (...
#   ...
#   '(?P<new_field_name>.*)' + DEL
#   ')')
#
# Example match: ''
PARSER_RE_STRING = ('(' + DEL + '(?P<commit>.*)' + DEL
    + '(?P<author_name>.*)' + DEL
    + '(?P<author_date>.*)' + DEL
    + '(?P<commit_date>.*)' + DEL
    + '(?P<author_email>.*)' + DEL
    + '(?P<subject>.*)' + DEL
    + ')')
PARSER_RE = re.compile(PARSER_RE_STRING, re.VERBOSE)


#
# This class clones a repository (GIT) using a provided URL and credential
# and proceeds to execute git log on it to scan its data
#
class Scanner:

    # -----------------------------------------------------------------
    # Adds the github username into the URL, taken from Vespene code
    def fix_repo_url(repo_url, cred):
        username = cred.username
        if username != '':
            if "@" not in repo_url:
                for prefix in GIT_TYPES:
                    if repo_url.startswith(prefix):
                        repo_url = repo_url.replace(prefix, "")
                        return "%s%s@%s" % (prefix, username, repo_url)
        return repo_url

    # ------------------------------------------------------------------
    # Entrypoint method which calls the clone and scan methods
    @transaction.atomic
    def scan_repo(repo, name, cred):
        repo_url = repo.url
        # Calculate the work directory by translating up two directories from this file
        #   eventually make this a settings variable so users can store it wherever
        work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        os.system('mkdir -p ' + work_dir)

        if name is None:
            repo_name = repo_url.rsplit('/', 1)[1]
        else:
            repo_name = name
        repo_instance = Scanner.clone_repo(repo_url, work_dir, repo_name, cred)
        Scanner.log_repo(repo, work_dir, repo_name, repo_instance)

    # ------------------------------------------------------------------
    # Clones the repo if it doesn't exist in the work folder and pulls if it does
    def clone_repo(repo_url, work_dir, repo_name, cred):

        # FIXME: need to use my git class?

        key_mgmt = None
        options = ""
        repo_obj = Repository.objects.get(name=repo_name)
        repo_url = repo_obj.url

        # If a credential was provided, add the password in an expect file to the git config
        if cred is not None:
            repo_url = Scanner.fix_repo_url(repo_url, cred)

        dest_path = os.path.join(work_dir, repo_name)

        dest_git = os.path.join(dest_path, ".git")

        if repo_url.startswith("ssh://"):
            key_mgmt = {
                "GIT_SSH_COMMAND": "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no",
            }
            if not cred or not cred.ssh_private_key:
                raise Exception(
                    "add one or more SSH keys to the repo's assigned credential object or use a http:// or https:// URL")

        if os.path.isdir(dest_path) and os.path.exists(dest_path) and os.path.exists(dest_git):

            prev = os.getcwd()
            os.chdir(dest_path)
            # FIXME: command wrapper should take an optional cwd
            commands.execute_command(repo_obj, "git pull", timeout=200, env=key_mgmt)
            os.chdir(prev)

        else:

            print("CREATING: %s" % dest_path)
            # os.makedirs can be a flakey in OS X, so shelling out
            commands.execute_command(repo_obj, "mkdir -p %s" % dest_path, log=True, timeout=5)

            # on-disk repo doesn't exist yet, need to clone
            # FIXME: refactor into smaller functions

            key_mgmt = None
            cmd = f"git clone {repo_url} {dest_path} {options}"



            commands.execute_command(repo_obj, cmd, log=False, timeout=600, env=key_mgmt)




        return repo_obj

    # ------------------------------------------------------------------
    # Uses git log to gather the commit data for a repository
    def log_repo(repo, work_dir, repo_name, repo_instance):

        # FIXME: refactor this into two files, splitting the logger and the checkout code

        repo_url = repo.url
        status_count = 0
        width_count = 0
        line_count = 0

        repo_dir = os.path.join(work_dir, repo_name)

        # python subprocess iteration doesn't have an EOF indicator that I can find.
        # We echo "EOF" to the end of the log output so we can tell when we are done
        cmd_string = ('git log --all --numstat --date=iso-strict-local --pretty=format:'
                      + PRETTY_STRING + '; echo "\nEOF"')
        # FIXME: as with above note, make command wrapper understand chdir
        prev = os.getcwd()
        os.chdir(repo_dir)

        if repo_name == "warpseq":
            print("HEY I AM RUNNING!")

        out = commands.execute_command(repo, cmd_string, log=False, timeout=600)
        os.chdir(prev)

        # Parsing happens in two stages. The first stage is a pretty string containing easily parsed fields for
        # the commit and author objects. The second stage processes lines added and removed for the current
        # commit. Pretty string is parsed using the regex PARSER_RE
        #
        # First stage:
        # DEL%HDEL%anDEL...
        #
        # Second Stage (lines added  lines removed     filename):
        # 2       0       README.md
        # ...
        #
        # The _flag booleans control which stage we are in. Once a pretty string
        # is read we switch to stage two (files_flag) Because files will point to their
        # commit, we keep a record of the "last" commit for when we are in files mode

        # currently parsing with regular expressions
        re_flag = True
        # last commit (for file objects)
        last_commit = {}
        # currently parsing files
        files_flag = False

        # PARSER ----------------------------------------------

        # FIXME: this doesn't really "stream" the output but in practice should not matter, if it does, revisit
        # later and add some new features to the commands wrapper
        # FIXME: consider alternative approaches to delimiter parsing, make this more modular

        lines = out.split("\n")


        for line in lines:

            # escape the empty line(s)
            if not line or line == "\n":
                continue

            # split a maximum of 1 time to efficiently find if the line is EOF
            if line.split(maxsplit=1)[0] == 'EOF':
                break

            # if the first character is '{', then we are no longer parsing files
            # we should drop through to stage 1 so that we can process this line as json
            if line[0:len(DEL)] == DEL:
                # clear last commit so that we don't accidentaly tie things to the wrong commit
                last_commit = {}
                files_flag = False

            # STAGE 2 -----------------------------------------
            if files_flag:
                fields = line.split()
                binary = False

                # binary files will have '-' in their field changes. Set these to 0
                if fields[1] == '-':
                    binary = True
                    fields[1] = 0
                if fields[0] == '-':
                    binary = True
                    fields[0] = 0

                # increment the files lines added/removed
                Creator.create_file(fields[2], last_commit, fields[0], fields[1], binary)

                # WARNING: this will record a huge amount of data
                if settings.RECORD_FILE_CHANGES:
                    #                   name       commit       lines add  lines rm
                    Creator.create_filechange(fields[2], last_commit, fields[0], fields[1], binary)

            print("RE_FLAG=%s" % re_flag)
            # STAGE 1 -----------------------------------------
            if re_flag:
                data = PARSER_RE.match(line).groupdict()

                author_instance = Creator.create_author(data['author_email'], repo_instance)
                commit_instance, created = Creator.create_commit(repo_instance,
                                                                 data["subject"],
                                                                 author_instance,
                                                                 data['commit'],
                                                                 parse_datetime(data['commit_date']),
                                                                 parse_datetime(data['author_date']), 0, 0)
                print("CREATED COMMIT=%s" % commit_instance)


                # if we have seen this commit before, causing it to
                # not be created
                if not created:
                    print("Stopping at previously scanned commit " + commit_instance.sha)
                    break

                # hand off control to file parsing
                re_flag = False
                last_commit = commit_instance
                files_flag = True

                # "print cute dots"
                status_count += 1
                if status_count > settings.DOTS_THRESHOLD:
                    print('.', end='')
                    status_count = 0
                    width_count += 1
                    # line wrap
                    if width_count > settings.DOTS_WIDTH:
                        line_count += 1
                        width_count = 0
                        print(str(line_count * settings.DOTS_THRESHOLD * settings.DOTS_WIDTH) + '\n')

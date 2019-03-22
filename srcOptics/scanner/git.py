import os
import subprocess
import getpass
import re
import datetime

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.conf import settings
from srcOptics.models import *
from srcOptics.create import Creator
from django.db import transaction

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

class Scanner:
    # -----------------------------------------------------------------
    # adds the github username into the https URL
    def fix_repo_url(repo_url, username):
        if username != '':
            if "@" not in repo_url:
                for prefix in GIT_TYPES:
                    if repo_url.startswith(prefix):
                        repo_url = repo_url.replace(prefix, "")
                        return "%s%s@%s" % (prefix, username, repo_url)
        return repo_url

    # ------------------------------------------------------------------
    @transaction.atomic
    def scan_repo(repo_url, cred):
        work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        os.system('mkdir -p ' + work_dir)
        repo_name = repo_url.rsplit('/', 1)[1]

        repo_instance, updated = Scanner.clone_repo(repo_url, work_dir, repo_name, cred)
        Scanner.log_repo(repo_url, work_dir, repo_name, repo_instance)



    # ------------------------------------------------------------------
    def clone_repo(repo_url, work_dir, repo_name, cred):

        updated = 0

        options = ""
        repo_instance = Creator.create_repo('root', repo_url, repo_name, cred)

        if cred is not None:
            options += ' --config core.askpass=\'' + cred.expect_pass() + '\''
            repo_url = Scanner.fix_repo_url(repo_url, cred.username)

        if os.path.isdir(work_dir + '/' + repo_name) and os.path.exists(work_dir + '/' + repo_name):
            cmd = subprocess.Popen('git pull' + options, shell=True, stdout=subprocess.PIPE, cwd=work_dir + '/' + repo_name)
            # TODO: Need to find a better solution for checking if its up to date
            for line in cmd.stdout:
                line = line.decode('utf-8')
                if "Already up to date." in line:
                    updated = 1
                    break
            print('git pull ' + repo_url + ' ' + work_dir)
        else:
            os.system('git clone ' + repo_url + ' ' + work_dir + '/' + repo_name + options)
            print('git clone ' + repo_url + ' ' + work_dir + '/' + repo_name + options)

        # TODO: Using literal string root for now...
        #repo_instance = Creator.create_repo('root', repo_url, repo_name, cred)
        return repo_instance, updated

    # ------------------------------------------------------------------
    def log_repo(repo_url, work_dir, repo_name, repo_instance):
        # python subprocess iteration doesn't have an EOF indicator that I can find.
        # We echo "EOF" to the end of the log output so we can tell when we are done
        cmd_string = ('git log --all --numstat --date=iso-strict-local --pretty=format:'
                      + PRETTY_STRING + '; echo "\nEOF"')
        cmd = subprocess.Popen(cmd_string, shell=True, stdout=subprocess.PIPE, cwd=work_dir + '/' + repo_name)

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
        for line in iter(cmd.stdout.readline,''):
            line = line.decode('utf-8')

            # escape the empty line(s)
            if not line or line == "\n":
                continue

            # split a maximum of 1 time to efficiently find if the line is EOF
            if line.split(maxsplit=1)[0] == 'EOF':
                break

            # if the first character is '{', then we are no longer parsing files
            # we should drop through to stage 1 so that we can process this line as json
            if line[0:len(DEL)] == DEL:
                re_flag = True
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


                # if we have seen this commit before, causing it to
                # not be created
                if not created:
                    print("Stopping at previously scanned commit " + commit_instance.sha)
                    break

                # hand off control to file parsing
                re_flag = False
                last_commit = commit_instance
                files_flag = True

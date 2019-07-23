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
from django.utils.dateparse import parse_datetime

from ..models import File, FileChange, Commit, Author
from . import commands
import re
from django.conf import settings

# The parser will use regex to grab the fields from the
# github pretty print. Fields with (?P<name>) are the
# capture groups used to turn matching areas of the pretty
# string into entries in a dictionary. The parser wants the
# entire string in one line (it reads line by line)
#
# The delimitor (DEL) will separate each field to parse
DEL = '&DEL&>'

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


class Commits:

    """
    This class clones a repository (GIT) using a provided URL and credential
    and proceeds to execute git log on it to scan its data
    """

    @classmethod
    def process_commits(cls, repo, repo_dir):

        """
        Uses git log to gather the commit data for a repository
        """
        # python subprocess iteration doesn't have an EOF indicator that I can find.
        # We echo "EOF" to the end of the log output so we can tell when we are done
        cmd_string = ('git log --all --numstat --date=iso-strict-local --pretty=format:'
                      + PRETTY_STRING + '; echo "\nEOF"')
        # FIXME: as with above note, make command wrapper understand chdir
        prev = os.getcwd()
        os.chdir(repo_dir)


        out = commands.execute_command(repo, cmd_string, log=False, timeout=600)
        os.chdir(prev)

        # Parsing happens in two stages for each commit.
        #
        # The first stage is a pretty string containing easily parsed fields for
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
        # Because files will point to their
        # commit, we keep a record of the "last" commit for when we are in files mode

        last_commit = None


        # FYI: this doesn't really "stream" the output but in practice should not matter, if it does, revisit
        # later and add some new features to the commands wrapper
        # FIXME: consider alternative approaches to delimiter parsing?

        if "does not have any commits yet" in out:
            print("skipping, no commits yet")
            return False

        lines = out.split("\n")

        for line in lines:

            # ignore empty lines
            if not line or line == "\n":
                continue

            # we are at the end of all output (FIXME: why do we need this?)
            if line.split(maxsplit=1)[0] == 'EOF':
                break

            if line.startswith(DEL):
                commit, created = cls.handle_diff_information(repo, line)
                last_commit = commit
                if not created:
                    # we've seen this commit before, so we're done
                    break
            else:
                cls.handle_file_information(repo, line, last_commit)

        return True

    # This assumes that commits (and their effect on files) will not be processed
    # more than once. It is on the scanner (the caller) to never scan commits
    # more than once.
    # ------------------------------------------------------------------
    @classmethod
    def create_file(cls, path, commit, la, lr, binary):
        file_instance = {}
        #get the file name
        fArray = os.path.basename(path)

        fName = ""
        if len(fArray) > 1:
            fName = fArray[1]
        else:
            fName = fArray[0]

        # find the extension
        (root, ext) = os.path.splitext(path)

        # update the global file object with the line counts
        file_instance,created = File.objects.get_or_create(path=path, defaults={
                    "lines_added":int(la),
                    "lines_removed":int(lr),
                    "name":fName,
                    "commit":commit,
                    "repo":commit.repo,
                    "binary":binary,
                    "ext":ext})

        # update the la/lr if we found the file
        if not created:
                file_instance.lines_added += int(la)
                file_instance.lines_removed += int(lr)
                file_instance.save()

        # add the la/lr to the commit for its total count
        commit.lines_added += int(la)
        commit.lines_removed += int(lr)
        commit.files.add(file_instance)
        commit.save()
        return file_instance

    @classmethod
    def create_filechange(cls, path, commit, la, lr, binary):
        # find the extension
        (root, ext) = os.path.splitext(path)

        # get the file name
        fArray = os.path.basename(path)

        fName = ""
        if len(fArray) > 1:
            fName = fArray[1]
        else:
            fName = fArray[0]

        filechange_instance = FileChange.objects.create(name=fName, path=path, ext=ext, commit=commit,
                                                            repo=commit.repo, lines_added=la, lines_removed=lr,
                                                            binary=binary)

        # add the file change to the global file object
        file_instance = File.objects.get(name=fName, path=path)
        file_instance.changes.add(filechange_instance)
        file_instance.save()

        return filechange_instance

    @classmethod
    def handle_file_information(cls, repo, line, last_commit):

        """
        process the list of file changes in this commit
        """


        # FIXME: give all these fields names
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
        cls.create_file(fields[2], last_commit, fields[0], fields[1], binary)

        # WARNING: this will record a huge amount of data
        if settings.RECORD_FILE_CHANGES:
            #                   name       commit       lines add  lines rm
            cls.create_filechange(fields[2], last_commit, fields[0], fields[1], binary)

    @classmethod
    def handle_diff_information(cls, repo, line):

        """
        process the amount of lines changed in this commit
        """


        # FIXME: give all these fields names
        match = PARSER_RE.match(line)
        if not match:
            raise Exception("DOESN'T MATCH? %s" % line)

        data = match.groupdict()
        email = data['author_email']

        author, created = Author.objects.get_or_create(email=email)
        author.repos.add(repo)
        author.save()

        commit_date = parse_datetime(data['commit_date'])
        author_date = parse_datetime(data['author_date'])
        commit, created = Commit.objects.get_or_create(
            sha=data['commit'],
            defaults=dict(
                subject=data['subject'],
                repo=repo,
                author=author,
                author_date=author_date,
                commit_date=commit_date,
                lines_added=0,
                lines_removed=0
            )
        )

        return commit, created

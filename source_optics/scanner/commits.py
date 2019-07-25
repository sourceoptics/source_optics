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
import fnmatch
from ..models import File, FileChange, Commit, Author
from . import commands
import re
from django.conf import settings

# we use git --log with a special one-line format string to capture certain fields
# we regex across those fields with a custom delimiter to make it easy to find them

DEL = '&DEL&>'

# Fields recorded (in order)
# commit hash %H
# author_name %an
# author_date %ad
# commit_date %cd
# author_email %ae
# subject %f

PRETTY_STRING = f"'{DEL}%H{DEL}%an{DEL}%ad{DEL}%cd{DEL}%ae{DEL}%f{DEL}'"

# the regex to match the string, which must watch the log format PRETTY_STRING

PARSER_RE_STRING = f"{DEL}(?P<commit>.*){DEL}(?P<author_name>.*){DEL}(?P<author_date>.*){DEL}(?P<commit_date>.*){DEL}(?P<author_email>.*){DEL}(?P<subject>.*){DEL}"

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
        cmd_string = ('git log --all --numstat --date=iso-strict-local --pretty=format:'
                      + PRETTY_STRING)

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

            if line.startswith(DEL):
                commit, created = cls.handle_diff_information(repo, line)
                if commit != last_commit and last_commit:
                    last_commit.save()
                if not created:
                    # we've seen this commit before, so we don't need to do any more scanning
                    break
            else:
                cls.handle_file_information(repo, line, last_commit)
        last_commit.save()
        return True

    # This assumes that commits (and their effect on files) will not be processed
    # more than once. It is on the scanner (the caller) to never scan commits
    # more than once.
    # ------------------------------------------------------------------
    @classmethod
    def create_file(cls, full_path, commit, la, lr, binary):
        file_instance = {}
        fname = os.path.basename(full_path)

        # find the extension
        (_, ext) = os.path.splitext(full_path)
        path = os.path.dirname(full_path)

        # update the global file object with the line counts
        file, created = File.objects.get_or_create(commit=commit, path=path, name=fname, ext=ext, defaults=dict(
            binary=binary
        ))

        # update the la/lr if we found the file
        if created:
            commit.files.add(file)


        file_change, created = FileChange.objects.get_or_create(file=file, commit=commit,
                defaults = dict(lines_added=la, lines_removed=lr))

        # add the file change to the global file object
        if created:
            file.changes.add(file_change)
            file.save()

        return file

    @classmethod
    def matches(self, needle, haystack, exact=False, trim_dot=False):

        #  user input may be inconsistent about trailing slashes so be flexible
        if haystack.endswith("/"):
            haystack = haystack[:-1]
        if needle.endswith("/"):
            needle = needle[:-1]



        if trim_dot:
            # for extension checking, do not require the user input to be ".mp4" to mean "mp4"
            haystack = haystack.replace(".","")
            needle = needle.replace(".", "")

        if "?" in needle or "*" in needle or "[" in needle:
            # this looks like a fnmatch pattern
            return fnmatch.fnmatch(haystack, needle)
        elif exact:
            # we are processing an extension, require an exact match
            return haystack == needle
        else:
            # we are processing paths, not extensions, so just require it to start with the substring
            return haystack.startswith(needle)

    @classmethod
    def has_matches(cls, needles, haystack, exact=False, trim_dot=False):

        for needle in needles:
            if cls.matches(needle, haystack, exact=exact, trim_dot=trim_dot):
                return True
        return False

    @classmethod
    def has_no_matches(cls, needles, haystack, exact=False, trim_dot=False):
        return not cls.has_matches(needles, haystack, exact=exact, trim_dot=trim_dot)

    @classmethod
    def repair_move_path(cls, path):
        # handle details about moves in git log by fixing path elements like /{org=>com}/
        # to just log the file in the final path. This will possibly give users credit for
        # aspects of a move but this something we can explore later. Not sure if it does - MPD.
        if "{" in path:
            # DO STUFF
            tokens = os.path.split(path)
            results = []
            for token in tokens:
                if token.startswith("{") and token.endswith("}") and "=>" in token:
                    correct = token[1:-1].split("=>")[-1]
                    print("corrected path segment=%s" % correct)
                    results.push(correct)
                else:
                    results.push(token)

            return os.path.join(results)
        return path

    @classmethod
    def should_process_path(cls, repo, path):

        org = repo.organization
        directory_allow = repo.scanner_directory_allow_list or org.scanner_directory_allow_list
        directory_deny  = repo.scanner_directory_deny_list or org.scanner_directory_deny_list

        extension_allow = repo.scanner_extension_allow_list or org.scanner_extension_allow_list
        extension_deny = repo.scanner_extension_deny_list or org.scanner_extension_deny_list

        dirname = os.path.dirname(path)
        split_ext = os.path.splitext(path)

        extension = None
        if len(split_ext) > 1:
            extension = split_ext[-1]

        if directory_allow:
            directory_allow = directory_allow.split("\n")
        if directory_deny:
            directory_deny = directory_deny.split("\n")
        if extension_allow:
            extension_allow = extension_allow.split("\n")
        if extension_deny:
            extension_deny = extension_deny.split("\n")


        if directory_allow and cls.has_no_matches(directory_allow, dirname):
            return False

        if directory_deny and cls.has_matches(directory_deny, dirname):
            return False

        if extension:
            if extension_allow and cls.has_no_matches(extension_allow, extension, exact=True, trim_dot=True):
                return False

            if extension_deny and cls.has_matches(extension_deny, extension, exact=True, trim_dot=True):
                return False

        return True

    @classmethod
    def handle_file_information(cls, repo, line, last_commit):

        """
        process the list of file changes in this commit
        """

        tokens = line.split()
        (added, removed, path) = (tokens[0], tokens[1], ''.join(tokens[2:]))

        # binary files will have '-' in their field changes. Set these to 0
        binary = False
        if added == '-':
            binary = True
            added = 0
        if removed == '-':
            binary = True
            removed = 0

        # FIXME: implement!
        path = cls.repair_move_path(path)

        if not cls.should_process_path(repo, path):
            return None

        # increment the files lines added/removed
        file = cls.create_file(path, last_commit, added, removed, binary)

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

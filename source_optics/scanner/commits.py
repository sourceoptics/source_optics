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

FILES_HACK_REPO = None
FILES_HACK = dict()


class Commits:

    """
    This class clones a repository (GIT) using a provided URL and credential
    and proceeds to execute git log on it to scan its data
    """

    @classmethod
    def get_file(cls, repo, path, filename):
        global FILES_HACK_REPO
        global FILES_HACK
        if FILES_HACK_REPO != repo.name:
            FILES_HACK = dict()
            FILES_HACK_REPO = repo.name
            files = File.objects.filter(repo=repo).all()
            for fobj in files:
                key = os.path.join(fobj.path, fobj.name)
                FILES_HACK[key] = fobj
        else:
            original = os.path.join(path, filename)
            return FILES_HACK[original]

    @classmethod
    def bulk_create(cls, total_commits, total_files, total_file_changes):
        # by not ignoring conflicts, we can test whether our scanner "overwork" code is correct
        # use -F to try a full test from scratch
        Commit.objects.bulk_create(total_commits, 5000, ignore_conflicts=True)
        del total_commits[:]
        File.objects.bulk_create(total_files, 5000, ignore_conflicts=True)
        del total_files[:]
        FileChange.objects.bulk_create(total_file_changes, 5000, ignore_conflicts=True)
        del total_file_changes[:]

    @classmethod
    def process_commits(cls, repo, repo_dir, mode='Commit'):

        """
        Uses git log to gather the commit data for a repository
        """

        cmd_string = 'git rev-list --all --count'
        commit_total = commands.execute_command(repo, cmd_string, log=False, timeout=600, chdir=repo_dir, capture=True)

        try:
            commit_total = int(commit_total)
        except TypeError:
            print("no commits yet")
            return

        cmd_string = ('git log --all --numstat --date=iso-strict-local --pretty=format:'
                      + PRETTY_STRING)


        last_commit = None
        count = 0
        total_commits = []
        total_file_changes = []
        total_files = []

        global GLITCH_COUNT

        def handler(line):

            nonlocal last_commit
            nonlocal count

            if count % 50 == 0:
                print("scanning (repo:%s) (mode:%s): %s/%s" % (repo, mode, count, commit_total))
            if count % 500 == 0:
                cls.bulk_create(total_commits, total_files, total_file_changes)

            if not line or line == "\n":
                #print("F1")
                return True # continue


            elif line.startswith(DEL):

                commit = cls.handle_diff_information(repo, line, mode)
                if last_commit != commit:
                    count = count + 1
                    last_commit = commit
                    total_commits.append(commit)
                return True

            elif "does not have any commits yet" in line:
                #print("skipping, no commits yet")
                return False

            else:
                if mode != 'Commit':
                    cls.handle_file_information(repo, line, last_commit, mode, total_files, total_file_changes)
                return True


        commands.execute_command(repo, cmd_string, log=False, timeout=1200, chdir=repo_dir, handler=handler)
        cls.bulk_create(total_commits, total_files, total_file_changes)

        return True

    # This assumes that commits (and their effect on files) will not be processed
    # more than once. It is on the scanner (the caller) to never scan commits
    # more than once.
    # ------------------------------------------------------------------
    @classmethod
    def create_file(cls, full_path, commit, la, lr, binary, mode, total_files, total_file_changes):

        fname = os.path.basename(full_path)

        # find the extension
        (_, ext) = os.path.splitext(full_path)
        path = os.path.dirname(full_path)

        if mode == 'File':

            # update the global file object with the line counts

            f = File(
                repo=commit.repo,
                path=path,
                name=fname,
                ext=ext,
                binary=binary
            )
            total_files.append(f)

            # BOOKMARK

        elif mode == 'FileChange':

            file = cls.get_file(commit.repo, path, fname)

            # FIXME: I think this is because of the fix_path function and moves, so a temporary hack only!
            if file is None:
                print("********************* GLITCH: %s/%s" % (path, fname))
                return

            fc = FileChange(
                    commit=commit,
                    lines_added=la,
                    lines_removed=lr,
                    file=file
            )
            total_file_changes.append(fc)


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

        # FIXME: this doesn't work because more than just one path segment can appear here
        # like /{/foo/bar=>baz/blorp}/ so this code still needs upgrades!

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
                    results.append(correct)
                else:
                    results.append(token)

            return os.path.sep.join(results)
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
    def handle_file_information(cls, repo, line, last_commit, mode, total_files, total_file_changes):

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
        added = int(added)
        removed = int(removed)

        path = cls.repair_move_path(path)

        if not cls.should_process_path(repo, path):
            return None

        cls.create_file(path, last_commit, added, removed, binary, mode, total_files, total_file_changes)

    @classmethod
    def handle_diff_information(cls, repo, line, mode):

        """
        process the amount of lines changed in this commit
        """


        # FIXME: give all these fields names
        match = PARSER_RE.match(line)
        if not match:
            raise Exception("DOESN'T MATCH? %s" % line)

        data = match.groupdict()
        if mode != 'Commit':
            # running back through the logs to set up the file changes
            commit = Commit.objects.get(sha=data['commit'])
            return commit

        email = data['author_email']

        author, created = Author.objects.get_or_create(email=email)

        commit_date = parse_datetime(data['commit_date'])
        author_date = parse_datetime(data['author_date'])

        # will pass on to bulk_create
        return Commit(
            sha=data['commit'],
            subject=data['subject'],
            repo=repo,
            author=author,
            author_date=author_date,
            commit_date=commit_date
        )

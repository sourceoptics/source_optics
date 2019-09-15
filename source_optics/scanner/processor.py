# Copyright 2018-2019 SourceOptics Project Contributors
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

# FIXME: this class needs to be parameterized to run in a loop or run in a format more ameniable to cron, until then, it's been modified so the management
# command runs against all repos exactly once and stops.

# FIXME: you should be able to choose to run scans, aggregartions, or both, or pick a particular repo or list of repos by name

import fcntl
import os
import shutil
import sys
import time

from django.conf import settings
from django.utils import timezone

from source_optics.scanner.rollup import Rollup

from ..models import Commit, Repository, Statistic, File
from .checkout import Checkout
from .commits import Commits
from .ssh_agent import SshAgentManager


#
# Loop that checks for repositories that have been added and ready to scan
#
class RepoProcessor:

    threshold = 1 # 30
    repo_sleep = 5
    thread_sleep = 5

    @classmethod
    def lock(cls):
        """
        this is designed so you can put the scanner on cron vs systemd and if the process isn't done, you don't
        see a build-up of overzealous scanners all trying to do the same job
        """
        fname = settings.SCANNER_LOCK_FILE
        fh = open(fname, 'w+')
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print("Another scanner process is likely using the lockfile: %s" % fname)
            sys.exit(0)
        return fh

    @classmethod
    def unlock(cls, handle):
        fcntl.flock(handle, fcntl.LOCK_UN)

    @classmethod
    def scan(cls, organization_filter=None, repository_filter=None, force_nuclear_rescan=False):
        """
        The main method behind the repo scanning CLI command.
        """

        # REFACTOR: this lock should be a context manager (aka 'with')
        lock_handle = cls.lock()

        agent_manager = SshAgentManager()

        print("scanning repos")
        repos = Repository.objects
        if organization_filter:
            repos = repos.filter(organization__name__contains=organization_filter)
        if repository_filter:
            repos = repos.filter(name__contains=repository_filter)

        repos = repos.select_related('organization').all()

        for repo in repos:
            cls.process_repo(repo, agent_manager, force_nuclear_rescan)

        cls.unlock(lock_handle)

    @classmethod
    def force_nuclear_rescan(cls, repo):
        """
        A nuclear rescan is "-F", which deletes a lot of  objects and starts over with an erased
        repo.  It is more for testing/debugging than production usage.
        """
        repo.last_scanned = None
        repo.force_next_pull = True
        Commit.objects.filter(repo=repo).delete() # cascade everything else
        Statistic.objects.filter(repo=repo).delete()
        File.objects.filter(repo=repo).delete()
        repo.save()

    @classmethod
    def needs_rescan(cls, repo):
        if repo.force_next_pull:
            return True
        if repo.last_pulled is None:
            return True

        today = timezone.now()
        timediff = (today - repo.last_pulled).total_seconds() / 60.0
        return (timediff > settings.PULL_THRESHOLD)

    @classmethod
    def potentially_add_ssh_key(cls, repo, agent_manager):
        if "http://" in repo.url or "https://" in repo.url:
            return False
        if repo.organization.credential and repo.organization.credential.ssh_private_key:
            # print("ADDING KEY")
            agent_manager.add_key(repo, repo.organization.credential)
            return True
        else:
            # FIXME: add typed exceptions with try/catch, so the processor can try other repos
            raise Exception("Failed. The url for the repo '%s' does not start with http:// or https:// and no SSH key has been set for the organization" % repo.name)

    @classmethod
    def finalize_commit_scan_info(cls, repo, scan_time_start):
         repo.force_next_pull = False
         repo.save()

    @classmethod
    def compute_repo_aggregrate_stats(cls, repo):
         # Generate the statistics for the repository
         print("aggregating stats for " + str(repo))
         Rollup.rollup_repo(repo)

    @classmethod
    def checkout_and_read_commit_logs(cls, repo, work_dir):

        if not Checkout.clone_repo(repo, work_dir):
            print("problem with checkout, skipping")
            return False
        if not Commits.process_commits(repo, work_dir, mode='Commit'):
            print("problem analyzing commits, skipping")
            return False
        Commits.process_commits(repo, work_dir, mode='File')
        Commits.process_commits(repo, work_dir, mode='FileChange')

        return True

    @classmethod
    # @transaction.atomic - FIXME: disabled for testing, I think? Or why?
    def process_repo(cls, repo, agent_manager, force_nuclear_rescan):

        if force_nuclear_rescan or repo.force_nuclear_rescan:
            print("*** RESCAN WAS FORCED **")
            cls.force_nuclear_rescan(repo)


        if not cls.needs_rescan(repo):
            print("(updated enough, skipping)")
            return False

        added_ssh_key = cls.potentially_add_ssh_key(repo, agent_manager)

        print("scanning " + str(repo))
        scan_time_start = time.clock()

        base_dir = repo.organization.get_working_directory()
        work_dir = os.path.join(base_dir, repo.name)

        if repo.force_nuclear_rescan and os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
            repo.force_nuclear_rescan = False
            repo.save()

        # FIXME: use commands class
        os.system('mkdir -p ' + work_dir)

        if not cls.checkout_and_read_commit_logs(repo, work_dir):
            return False

        cls.finalize_commit_scan_info(repo, scan_time_start)

        if added_ssh_key:
            agent_manager.cleanup(repo)

        cls.compute_repo_aggregrate_stats(repo)

        return True

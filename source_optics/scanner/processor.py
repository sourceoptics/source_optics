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

# FIXME: this class needs to be parameterized to run in a loop or run in a format more ameniable to cron, until then, it's been modified so the management
# command runs against all repos exactly once and stops.

# FIXME: you should be able to choose to run scans, aggregartions, or both, or pick a particular repo or list of repos by name

import datetime
import fcntl
import os
import sys
import time

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from source_optics.scanner.rollup import Rollup

from ..models import Repository
from .checkout import Checkout
from .commits import Commits
from .ssh_agent import SshAgentManager


#
# Daemon that checks for repositories that have been added and enabled to scan
# A repo that is scanned recently is scanned after threshold time has passed
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
        except IOError as e:
            print("Another scanner process is likely using the lockfile: %s" % fname)
            sys.exit(0)
        return fh

    @classmethod
    def unlock(cls, handle):
        fcntl.flock(handle, fcntl.LOCK_UN)

    @classmethod
    def scan(cls, organization_filter=None):

        lock_handle = cls.lock()

        agent_manager = SshAgentManager()

        # FIXME: grab flock in case cron interval is too close

        print("processing repos...")

        repos = None
        if organization_filter:
            repos = Repository.objects.filter(organization__name__contains=organization_filter).all()
        else:
            repos = Repository.objects.all()

        # Check through every repository

        for repo in repos:


            used_ssh = False
            print("repo: %s" % repo)

            if not repo.enabled:
                print("(disabled, skipping)")
                continue

            # Calculate time difference based on last_pulled date
            today = datetime.datetime.now(tz=timezone.utc)
            if repo.last_pulled is not None:
                timediff = (today - repo.last_pulled).total_seconds() / 60.0
                if timediff < settings.PULL_THRESHOLD and not repo.force_next_pull:
                    print("(recently processed, skipping)")
                    continue


            if "http://" not in repo.url and "https://" not in repo.url:
                if repo.organization.credential and repo.organization.credential.ssh_private_key:
                    print("ADDING KEY")
                    agent_manager.add_key(repo, repo.organization.credential)
                    used_ssh = True
                else:
                    raise Exception("repo checkout of %s requires SSH credentials" % repo.name)


            # FIXME: better detection if a private repo
            # FIXME: refactor into smaller functions

            # Scan the repository and update the last pulled date
            print("Scanning " + str(repo))
            scan_time_start = time.clock()

            # FIXME: this should only take "repo" as a parameter.
            print("--- SCANNING: %s" % repo)

            # this is where the logging of commit objects happens
            ok = cls.scan_repo(repo)
            if not ok:
                print("problem scanning repo, skipping")
                continue

            # FIXME: refactor into smaller functions

            scan_time_total = time.clock() - scan_time_start
            print ("Scanning complete. Operation time for " + str(repo) + ": " + str(scan_time_total) + "s")
            repo.last_pulled = datetime.datetime.now(tz=timezone.utc)
            print("last_pulled: "  + str(repo.last_pulled))

            repo.force_next_pull = False
            repo.save()

            if used_ssh:
                # drop old keys
                agent_manager.cleanup(repo)

            # Generate the statistics for the repository
            print ("Aggregating stats for " + str(repo))
            stat_time_start = time.clock()
            Rollup.rollup_repo(repo)
            stat_time_total = time.clock() - stat_time_start
            print ("Rollup complete. Operation time for " + str(repo) + ": " + str(stat_time_total) + "s")

        cls.unlock(lock_handle)

    @classmethod
    @transaction.atomic
    def scan_repo(cls, repo):
        # Calculate the work directory by translating up two directories from this file
        #   eventually make this a settings variable so users can store it wherever

        work_dir = repo.organization.get_working_directory()
        work_dir = os.path.join(work_dir, repo.name)

        os.system('mkdir -p ' + work_dir)

        ok = Checkout.clone_repo(repo, work_dir)
        if not ok:
            print("problem with checkout, skipping")
            return False

        ok = Commits.process_commits(repo, work_dir)
        return ok

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
import time

from django.utils import timezone

from . git import Scanner
from .. stats.rollup import Rollup
from .. models import Repository
from . ssh_agent import SshAgentManager

#
# Daemon that checks for repositories that have been added and enabled to scan
# A repo that is scanned recently is scanned after threshold time has passed
#
class RepoProcessor:

    threshold = 1 # 30
    repo_sleep = 5
    thread_sleep = 5


    @classmethod
    def scan(cls):

        agent_manager = SshAgentManager()

        # FIXME: grab flock in case cron interval is too close

        print("Processing all repos...")

        repos = Repository.objects.all()

        # Check through every repository
        #TODO: probably should sort this by repos with least amt of commits first
        for repo in repos:

            used_ssh = False
            print("Repo: %s" % repo)

            if not repo.enabled:
                continue

            # Calculate time difference based on last_pulled date
            today = datetime.datetime.now(tz=timezone.utc)
            if repo.last_pulled is not None:
                timediff = (today - repo.last_pulled).total_seconds() / 60.0



            if "http://" not in repo.url and "https://" not in repo.url:
                if repo.cred and repo.cred.ssh_private_key:
                    print("ADDING KEY")
                    agent_manager.add_key(repo, repo.cred)
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
            Scanner.scan_repo(repo, repo.name, repo.cred)

            # FIXME: refactor into smaller functions

            scan_time_total = time.clock() - scan_time_start
            print ("Scanning complete. Operation time for " + str(repo) + ": " + str(scan_time_total) + "s")
            repo.last_pulled = datetime.datetime.now(tz=timezone.utc)
            print("last_pulled: "  + str(repo.last_pulled))
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



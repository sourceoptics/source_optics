# FIXME: this class needs to be parameterized to run in a loop or run in a format more ameniable to cron, until then, it's been modified so the management
# command runs against all repos exactly once and stops.

# FIXME: you should be able to choose to run scans, aggregartions, or both, or pick a particular repo or list of repos by name

import datetime
import time

from django.utils import timezone

from . git import Scanner
from .. stats.rollup import Rollup
from .. models import Repository

#
# Daemon that checks for repositories that have been added and enabled to scan
# A repo that is scanned recently is scanned after threshold time has passed
#
class Daemon:

    threshold = 1 # 30
    repo_sleep = 5
    thread_sleep = 5

    @classmethod
    def scan(cls):
        print("Starting scan loop...")

        while True:
            repos = Repository.objects.all()

            # Check through every repository
            #TODO: probably should sort this by repos with least amt of commits first
            for repo in repos:

                print("Repo: %s" % repo)

                # Calculate time difference based on last_pulled date
                today = datetime.datetime.now(tz=timezone.utc)
                if repo.last_pulled is not None:
                    timediff = (today - repo.last_pulled).total_seconds() / 60.0

                # For enabled repos that haven't been pulled since last threshold, scan and aggregate
                if repo.enabled == True: # and (repo.last_pulled is None or timediff > cls.threshold) :

                    # Scan the repository and update the last pulled date
                    print("Scanning " + str(repo))
                    scan_time_start = time.clock()
                    Scanner.scan_repo(repo.url, repo.name, repo.cred)
                    scan_time_total = time.clock() - scan_time_start
                    print ("Scanning complete. Operation time for " + str(repo) + ": " + str(scan_time_total) + "s")
                    repo.last_pulled = datetime.datetime.now(tz=timezone.utc)
                    print("last_pulled: "  + str(repo.last_pulled))
                    repo.save()

                    # Generate the statistics for the repository
                    print ("Aggregating stats for " + str(repo))
                    stat_time_start = time.clock()
                    Rollup.rollup_repo(repo)
                    stat_time_total = time.clock() - stat_time_start
                    print ("Rollup complete. Operation time for " + str(repo) + ": " + str(stat_time_total) + "s")

                # Wait some time after scanning each repo
                time.sleep(cls.repo_sleep)


            break

            # time.sleep(cls.thread_sleep)
            # print("Checking for new data...")

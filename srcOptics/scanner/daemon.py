import datetime
import time

from django.utils import timezone

from srcOptics.scanner.git import Scanner
from srcOptics.stats.rollup import Rollup
from srcOptics.models import Repository


# Daemon that checks for repositories that have been added and enabled to scan
class Daemon:

    threshold = 30
    repo_sleep = 60
    thread_sleep = 60

    @classmethod
    def scan(cls):
        print("Starting daemon...")
        while True:
            repos = Repository.objects.all()
            #TODO: probably should sort this by repos with least amt of commits first
            for repo in repos:
                today = datetime.datetime.now(tz=timezone.utc)
                if repo.last_pulled is not None:
                    timediff = (today - repo.last_pulled).total_seconds() / 60.0
                if repo.enabled == True and (repo.last_pulled is None or timediff > cls.threshold) :
                    print("Scanning " + str(repo))
                    scan_time_start = time.clock()
                    Scanner.scan_repo(repo.url, repo.cred)
                    scan_time_total = time.clock() - scan_time_start
                    print ("Scan time for " + str(repo) + ": " + str(scan_time_total) + "s")
                    print ("Aggregating stats for " + str(repo))
                    stat_time_start = time.clock()
                    Rollup.rollup_repo(repo)
                    stat_time_total = time.clock() - stat_time_start
                    print ("Rollup time for " + str(repo) + ": " + str(stat_time_total) + "s")
                time.sleep(cls.repo_sleep)
            time.sleep(cls.thread_sleep)
            print("Checking for new data...")

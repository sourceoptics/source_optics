from django.test import TransactionTestCase, TestCase
from . models import *
from . scanner.git import Scanner
from . stats.rollup import Rollup
from datetime import date, datetime

from django.utils import timezone
from django.db.models import Sum

import subprocess
import os

REPO ='https://github.com/srcoptics/demorepo'
REPO_NAME = "demorepo"

class RollupTest(TransactionTestCase):

    def init(self):
        #work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        #rm_process = subprocess.Popen("rm -rf " + work_dir)
        #rm_process.wait()
        Organization.objects.create(name="root")

    def scan(self):
        # our test login information
        cred = LoginCredential(name='demouser', username='srcoptics', password='bigbig2019')
        cred.save()
        # Scan our demo repo
        Scanner.scan_repo(REPO, None, cred)

    def rollup(self):
        repo = Repository.objects.get(name=REPO_NAME)
        Rollup.rollup_repo(repo)

    def assert_commit(self, commit, sha, subject, author, la, lr):
        self.assertEqual(commit.subject, subject)
        self.assertEqual(commit.sha, sha)
        self.assertEqual(commit.author.email, author)
        self.assertEqual(commit.lines_added, la)
        self.assertEqual(commit.lines_removed, lr)

    def assert_statistic(self, statistic, repo, author, la, lr, lc, at, ct):
        self.assertEqual(statistic.repo, repo)
        self.assertEqual(statistic.lines_added, la)
        self.assertEqual(statistic.lines_removed, lr)
        self.assertEqual(statistic.lines_changed, lc)
        self.assertEqual(statistic.author_total, at)
        self.assertEqual(statistic.commit_total, ct)

    def assert_aggregations(self, repo, author):
        print(repo.earliest_commit)
        first_day_week = Rollup.get_first_day(repo.earliest_commit, ('WK', "Week"))
        first_day_month = Rollup.get_first_day(repo.earliest_commit, ('MN', "Month"))

        today = datetime.now(tz=timezone.utc)

        day_lifetime = Statistic.objects.filter(interval='DY', repo=repo,
                                    author=author, file=None,
                                    start_date__range=(repo.earliest_commit, today))

        week_lifetime = Statistic.objects.filter(interval='WK', repo=repo,
                                    author=author, file=None,
                                    start_date__range=(first_day_week, today))

        month_lifetime = Statistic.objects.filter(interval='MN', repo=repo,
                                    author=author, file=None,
                                    start_date__range=(first_day_month, today))

        summary_stats_day = day_lifetime.aggregate(commits=Sum("commit_total"), authors=Sum("author_total"), lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"), lines_changed=Sum("lines_changed"))

        summary_stats_week = week_lifetime.aggregate(commits=Sum("commit_total"), authors=Sum("author_total"), lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"), lines_changed=Sum("lines_changed"))

        summary_stats_month = month_lifetime.aggregate(commits=Sum("commit_total"), authors=Sum("author_total"), lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"), lines_changed=Sum("lines_changed"))

        self.assertEqual(summary_stats_day['commits'], summary_stats_week['commits'])
        #Author count doesn't make sense for author statistics
        if author is None:
            self.assertEqual(summary_stats_day['authors'], summary_stats_week['authors'])
        self.assertEqual(summary_stats_day['lines_added'], summary_stats_week['lines_added'])
        self.assertEqual(summary_stats_day['lines_removed'], summary_stats_week['lines_removed'])
        self.assertEqual(summary_stats_day['lines_changed'], summary_stats_week['lines_changed'])

        self.assertEqual(summary_stats_day['commits'], summary_stats_month['commits'])

        #Author count doesn't make sense for author statistics
        if author is None:
            self.assertEqual(summary_stats_day['authors'], summary_stats_month['authors'])
        self.assertEqual(summary_stats_day['lines_added'], summary_stats_month['lines_added'])
        self.assertEqual(summary_stats_day['lines_removed'], summary_stats_month['lines_removed'])
        self.assertEqual(summary_stats_day['lines_changed'], summary_stats_month['lines_changed'])

    # Verify that statistics for a scanned repo are generated appropriately after
    # checking that the repo was scanned properly
    def test_rollup(self):
        self.init()
        self.scan()

        # Verify initial commit
        #one = Commit.objects.get(sha="d76f7f8a7c0b7a8875fdcea54107739697fcd82b")
        #self.assert_commit(commit=one, sha="d76f7f8a7c0b7a8875fdcea54107739697fcd82b",
        #                   subject="Initial-commit", author="47673373+srcoptics@users.noreply.github.com", la=2, lr=0)

        # Rollup data for scanned repo
        with self.settings(MULTITHREAD_AGGREGATE=False):
            self.rollup()

        # Verify some generated total statistics
        repo = Repository.objects.get(name=REPO_NAME)
        #first_date = date(2019, 2, 15)
        #total_statistic = Statistic.objects.get(repo=repo, interval="DY", author=None, start_date__contains=first_date)
        #self.assert_statistic(statistic=total_statistic, repo=repo, author=None, la=2, lr=0, lc=2, at=1, ct=1)
        self.assert_aggregations(repo=repo, author=None)

        author = Author.objects.get(email="afranci@ncsu.edu")
        self.assert_aggregations(repo=repo, author=author)
        #author_statistic = Statistic.objects.get(repo=repo, interval="DY", author=author, start_date__contains=first_date)
        #self.assert_statistic(statistic=author_statistic, repo=repo, author=author, la=2, lr=0, lc=2, at=1, ct=1)

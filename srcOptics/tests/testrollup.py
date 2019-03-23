from django.test import TestCase
from srcOptics.models import *
from srcOptics.scanner.git import Scanner
from srcOptics.stats.rollup import Rollup
from datetime import date
import subprocess
import os

REPO ='https://github.com/srcoptics/srcoptics_test'
REPO_NAME = "srcoptics_test"

class RollupTest(TestCase):

    def init(self):
        #work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        #rm_process = subprocess.Popen("rm -rf " + work_dir)
        #rm_process.wait()
        Organization.objects.create(name="root")
    
    def scan(self):
        # our test login information
        cred = LoginCredential(username='srcoptics', password='bigbig2019')
        cred.save()
        # Scan our demo repo
        Scanner.scan_repo(REPO, cred)

    def rollup(self):
        repo = Repository.objects.get(name="")
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

    # Verify that statistics for a scanned repo are generated appropriately after
    # checking that the repo was scanned properly
    def test_rollup(self):
        self.init()
        self.scan()

        # Verify initial commit
        one = Commit.objects.get(sha="d76f7f8a7c0b7a8875fdcea54107739697fcd82b")
        self.assert_commit(commit=one, sha="d76f7f8a7c0b7a8875fdcea54107739697fcd82b",
                           subject="Initial-commit", author="47673373+srcoptics@users.noreply.github.com", la=2, lr=0)
        
        # Rollup data for scanned repo
        self.rollup()

        # Verify some generated total statistics
        repo = Repository.objects.get(name="")
        first_date = date(2019, 2, 15)
        total_statistic = Statistic.objects.get(repo=repo, interval="DY", author=None, start_date__contains=first_date)
        self.assert_statistic(statistic=total_statistic, repo=repo, author=None, la=2, lr=0, lc=2, at=1, ct=1)
        
        author = Author.objects.get(email="47673373+srcoptics@users.noreply.github.com")
        author_statistic = Statistic.objects.get(repo=repo, interval="DY", author=author, start_date__contains=first_date)
        self.assert_statistic(statistic=author_statistic, repo=repo, author=author, la=2, lr=0, lc=2, at=1, ct=1)

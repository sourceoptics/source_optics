from django.test import TestCase

from .models import *
from .scanner.git import Scanner

REPO_NAME='https://github.com/srcoptics/srcoptics_test'

class ScanTest(TestCase):

    def init(self):
        Organization.objects.create(name="root")

    def scan(self):
        # our test login information
        cred = LoginCredential(name='demouser',username='srcoptics', password='bigbig2019')
        cred.save()
        # run the end-to-end scanner
        Scanner.scan_repo(REPO_NAME, None, cred)

    def assert_commit(self, commit, sha, subject, author, la, lr):
        self.assertEqual(commit.subject, subject)
        self.assertEqual(commit.sha, sha)
        self.assertEqual(commit.author.email, author)
        self.assertEqual(commit.lines_added, la)
        self.assertEqual(commit.lines_removed, lr)


    # manually verify information we read was correct
    #
    # At time of writing we verify the first 2 commits. More
    # should be added later
    def test_scan(self):
        self.init()
        self.scan()

        # Verify initial commit
        one = Commit.objects.get(sha="d76f7f8a7c0b7a8875fdcea54107739697fcd82b")
        self.assert_commit(commit=one, sha="d76f7f8a7c0b7a8875fdcea54107739697fcd82b",
                           subject="Initial-commit", author="47673373+srcoptics@users.noreply.github.com", la=2, lr=0)

        readme = File.objects.get(path="README.md")
        self.assertEqual(readme.lines_added, 2)
        self.assertEqual(readme.ext, ".md")

        repos = Repository.objects.all()
        self.assertEqual(len(repos), 1)

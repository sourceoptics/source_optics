from django.test import TestCase
from srcOptics.models import *
from srcOptics.scanner.git import Scanner

REPO_NAME='https://github.com/srcoptics/srcoptics_test'

class ScanTest(TestCase):

    def init(self):
        Organization.objects.create(name="root")
    
    def scan(self):
        # our test login information
        cred = LoginCredential(username='srcoptics', password='bigbig2019')
        cred.save()
        # run the end-to-end scanner        
        Scanner.scan_repo(REPO_NAME, cred)

    # manually verify information we read was correct
    #
    # At time of writing we verify the first 2 commits. More
    # should be added later
    def test_scan(self):
        self.init()
        self.scan()
        
        # Verify initial commit
        one = Commit.objects.get(sha="d76f7f8a7c0b7a8875fdcea54107739697fcd82b")
        self.assertEqual(one.subject, "Initial-commit")

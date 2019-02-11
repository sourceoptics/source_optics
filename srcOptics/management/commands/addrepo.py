from django.core.management.base import BaseCommand, CommandError

from srcOptics.plugins.organizations.github import Scanner

from srcOptics.models import LoginCredential
import getpass

class Command(BaseCommand):
    help = 'Adds a repository to a queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_url', type=str, help='Repository url')
        
    def handle(self, *args, **kwargs):

        # get the VC credentials and make a LoginCredential before cloning
        username = input('Username: ')
        password = getpass.getpass('Password: ')
        cred = LoginCredential.objects.create(username=username, password=password)
        
        Scanner.scan_repo(kwargs['repo_url'], cred)
        #print(kwargs['repo_url'] + " added")

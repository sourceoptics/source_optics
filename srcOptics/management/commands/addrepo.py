from django.core.management.base import BaseCommand, CommandError

from srcOptics.scanner.git import Scanner

from srcOptics.models import LoginCredential
import getpass


#
# The addrepo management command is used to add a repository to the
# database. The user should pass in the URL as the only parameter
#
class Command(BaseCommand):
    help = 'Adds a repository to a queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_url', type=str, help='Repository url')
        
    def handle(self, *args, **kwargs):

        # get the VC credentials and make a LoginCredential before cloning
        username = input('Username: ')
        password = getpass.getpass('Password: ')
        cred = LoginCredential.objects.create(username=username, password=password)
        
        # Scan the repository, passing in the URL and LoginCredential
        Scanner.scan_repo(kwargs['repo_url'], None, cred)

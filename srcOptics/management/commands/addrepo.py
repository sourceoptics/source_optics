from django.core.management.base import BaseCommand, CommandError

from srcOptics.plugins.organizations.github import Scanner

class Command(BaseCommand):
    help = 'Adds a repository to a queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_url', type=str, help='Repository url')
        
    def handle(self, *args, **kwargs):
        Scanner.scan_repo(kwargs['repo_url'])
        #print(kwargs['repo_url'] + " added")

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Adds a statistics job for a given repository'

    def add_arguments(self, parser):
        parser.add_argument('repo_name', type=str, help='Repository name')
        
    def handle(self, *args, **kwargs):
        print("Generating statistics for " + kwargs['repo_name'] + "...")
from django.core.management.base import BaseCommand, CommandError
import os

class Command(BaseCommand):
    help = 'Adds a repository to a queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_url', type=str, help='Repository url')
        
    def handle(self, *args, **kwargs):

        work_dir = os.path.abspath(os.path.dirname(__file__).dirname().dirname())

        repo = kwargs['repo_url']
        repo_name = repo.rsplit('/', 1)[1]
        os.system('git clone ' + repo + ' ' + work_dir)
        print(repo + " added")

from django.core.management.base import BaseCommand, CommandError
import os


def clone_repo(repo_url):
    work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
    os.system('mkdir -p ' + work_dir)

    repo_name = repo_url.rsplit('/', 1)[1]
    print('git clone ' + repo_url + ' ' + work_dir)
    os.system('git clone ' + repo_url + ' ' + work_dir + '/' + repo_name)

class Command(BaseCommand):
    help = 'Adds a repository to a queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_url', type=str, help='Repository url')
        
    def handle(self, *args, **kwargs):

        clone_repo(kwargs['repo_url'])
        print(kwargs['repo_url'] + " added")

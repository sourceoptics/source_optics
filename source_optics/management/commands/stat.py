from django.core.management.base import BaseCommand, CommandError
from ... stats.rollup import Rollup
from ... models import *

#
# The stat management command is used to generate statistics for an
# already cloned repository. The user must provide the repository name
# as a single parameter.
#
class Command(BaseCommand):
    help = 'Generates tabular statistics off of the job queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_name', type=str, help='Repository Name')

    def handle(self, *args, **kwargs):
        repo = Repository.objects.get(name=kwargs['repo_name'])
        Rollup.rollup_repo(repo=repo)

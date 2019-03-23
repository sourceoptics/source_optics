from django.core.management.base import BaseCommand, CommandError
from srcOptics.stats.rollup import Rollup
from srcOptics.models import *

class Command(BaseCommand):
    help = 'Generates tabular statistics off of the job queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_name', type=str, help='Repository Name')

    def handle(self, *args, **kwargs):
        r = Repository.objects.get(name=kwargs['repo_name'])
        Rollup.rollup_repo(repo=r)

from django.core.management.base import BaseCommand, CommandError
from srcOptics.stats.rollup import Rollup


class Command(BaseCommand):
    help = 'Generates tabular statistics off of the job queue'

    def handle(self, *args, **kwargs):
        Rollup.rollup_repo()

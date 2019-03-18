from django.core.management.base import BaseCommand, CommandError

from srcOptics.scanner.daemon import Daemon

class Command(BaseCommand):
    help = 'Scans a repository off of the queue'

    def add_arguments(self, parser):
        parser.add_argument('-r', '--recursive', action='store_true', help='Scans through every branch in the repository')
        parser.add_argument('-s', '--store', action='store_true', help='Stores all SHA data in database')

    def handle(self, *args, **kwargs):
        Daemon.scan()

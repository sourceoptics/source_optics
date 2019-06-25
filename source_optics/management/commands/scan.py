from django.core.management.base import BaseCommand, CommandError

from ... scanner.daemon import Daemon

#
# The scan management command is used to kick of the daemon job which
# checks for enabled repositories which should be scanned and parsed
# for statistics 
#
class Command(BaseCommand):
    help = 'Scans a repository off of the queue'

    def handle(self, *args, **kwargs):
        Daemon.scan()

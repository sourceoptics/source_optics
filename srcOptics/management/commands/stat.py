from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Generates tabular statistics off of the job queue'
        
    def handle(self, *args, **kwargs):
        msg = "Generating statistics..."
        print(msg)
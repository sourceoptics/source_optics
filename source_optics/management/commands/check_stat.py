import fnmatch

from django.core.management.base import BaseCommand, CommandError
from github import Github

from ...models import Repository, Statistic

class Command(BaseCommand):
    help = 'dumps raw aggregated statistics from the database, mostly for debug purposes'

# EX: python manage.py check_stat -o root -r opsmop -i WK -a 'michael@michaeldehaan.net'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--organization', dest='organization', type=str, help='report stats on repos in this org name', default=None)
        parser.add_argument('-r', '--repo', dest='repo', type=str, help='report stats on this repo name', default=None)
        parser.add_argument('-a', '--author', dest='author', type=str, help='report stats on this email address', default=None)
        parser.add_argument('-i', '--interval', dest='interval', type=str, help='show reports for this interval (DY, WK, MN)', default='MN')

    def handle(self, *args, **kwargs):

        organization = kwargs['organization']
        repo = kwargs['repo']
        author = kwargs['author']
        interval = kwargs['interval']

        assert repo is not None
        assert organization is not None

        repo = Repository.objects.get(name=repo, organization__name=organization)

        stats = None
        if author:
            stats = Statistic.objects.filter(repo=repo, author__email=author, interval=interval)

        else:
            stats = Statistic.objects.filter(repo=repo, author__isnull=True, interval=interval)

        for stat in stats.all():
            print(f"{stat.start_date} : A:{stat.lines_added} R:{stat.lines_removed} C:{stat.commit_total}")


from django.db.models import Sum, Max
from ... models import Statistic, Commit

class Plugin(object):

    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None):

        data = dict()

        data['meta'] = dict(
            title = 'Repo Summary'
        )

        data['repos'] = dict()

        for repo in repos.all():

            item = data['repos'][repo.name] = dict()

            totals = Statistic.objects.filter(
                interval='DY', # control not needed here
                repo=repo,
                author__isnull=True,
                start_date__range=(start, end)
            ).aggregate(
                lines_added=Sum('lines_added'),
                lines_removed=Sum('lines_removed'),
                commits=Sum('commit_total'),
                authors=Max('author_total')
            )

            item['overall'] = dict(
                lines_added = totals['lines_added'],
                lines_removed = totals['lines_removed'],
                commits = totals['commits'],
                authors = totals['authors']
            )

            by_author = item['by_author'] = dict()

            author_ids = Commit.objects.filter(repo=repo).values_list('author__pk', flat=True).distinct().all()
            print(author_ids)

            repo_authors = authors.filter(pk__in=author_ids)

            for author in repo_authors.all():

                item = by_author[author.email] = dict()
                item['fixme'] = 1



        return data

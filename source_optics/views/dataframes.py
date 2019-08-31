import pandas as pd
from .. models import Statistic, Commit, Author, Repository
from django.db.models import Count, Sum
import datetime

def get_interval(start, end):
    # FIXME: this isn't quite a solid plan for educational vs corporate repos when people may want to zoom in.
    # it's good enough for now, but should probably evolve later to be web-configurable.
    delta = end-start
    if delta.days > 365:
        return 'WK'
    else:
        return 'DY'

def top_authors(repo, start, end, attribute='commit_total', limit=10):

    interval = get_interval(start, end)

    authors = []
    filter_set = Statistic.objects.filter(
        interval=interval,
        author__isnull=False,
        repo=repo,
        start_date__range=(start, end)
    ).values('author_id').annotate(total=Sum(attribute)).order_by('-total')[0:limit]

    author_ids = [ t['author_id'] for t in filter_set ]
    return author_ids


def _queryset_for_scatter(repo, start=None, end=None, by_author=False, interval='DY'):
    totals = None
    if not by_author:
        if interval != 'LF':
            totals = Statistic.objects.select_related('repo', ).filter(
                interval=interval,
                repo=repo,
                author__isnull=True,
                start_date__range=(start, end)
            )
        else:
            totals = Statistic.objects.select_related('repo').filter(
                interval=interval,
                repo=repo,
                author__isnull=True
            )
    else:
        top = top_authors(repo, start, end)
        if interval != 'LF':
            totals = Statistic.objects.select_related('repo', 'author').filter(
                interval=interval,
                repo=repo,
                author__pk__in=top,
                start_date__range=(start, end)
            )
        else:
            # note, this is used for slightly DIFFERENT purposes in the final graphs, so doesn't restrict
            # to the top authors list. If this ever becomes important, it might need to change.
            totals = Statistic.objects.select_related('repo', 'author').filter(
                interval=interval,
                repo=repo,
                author__isnull=False
                # author__pk__in=top
            )
    return totals.order_by('author','start_date')

def _scatter_queryset_to_dataframe(repo, totals, fields):
    data = dict()

    first_day = repo.earliest_commit_date()

    for f in fields:
        data[f] = []

    for t in totals:

        for f in fields:
            if f == 'date':
                # just renaming this one field for purposes of axes labelling
                data[f].append(t.start_date)
            elif f == 'day':
                data[f].append((t.start_date - first_day).days)
            elif f == 'author':
                data[f].append(t.author.email)
            else:
                data[f].append(getattr(t, f))

    return pd.DataFrame(data, columns=fields)

DEFAULT_SCATTER_FIELDS = [
    'date', 'day', 'lines_changed', 'commit_total', 'author_total', 'average_commit_size',
]
LIFETIME_ONLY_SCATTER_FIELDS = [
     'earliest_commit_date', 'latest_commit_date', 'days_since_seen',
     'days_before_joined', 'days_before_last', 'longevity', 'days_active'
]

def stat_series(repo, start=None, end=None, fields=None, by_author=False, interval=None):

    if not interval:
        interval = get_interval(start, end)

    if fields is None:
        fields = DEFAULT_SCATTER_FIELDS[:]
        if interval == 'LF':
            fields.extend(LIFETIME_ONLY_SCATTER_FIELDS)
        if by_author:
            fields.append('author')

    totals = _queryset_for_scatter(repo, start=start, end=end, by_author=by_author, interval=interval)
    return _scatter_queryset_to_dataframe(repo, totals, fields)




import pandas as pd
from .. models import Statistic, Commit, Author, Repository
from django.db.models import Count, Sum

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

def stat_series(repo, start=None, end=None, fields=None, by_author=False, interval=None):

    if not interval:
        interval = get_interval(start, end)

    if fields is None:
        if not by_author:
            fields = [ 'date', 'day', 'lines_changed', 'commit_total', 'author_total', 'average_commit_size' ]
        else:
            fields = [ 'date', 'day', 'author', 'lines_changed', 'commit_total', 'author_total', 'average_commit_size' ]
        if interval == 'LF':
            # these are only computed in lifetime mode as they don't really makes sense in time series...
            fields.append('earliest_commit_date')
            fields.append('latest_commit_date')
            fields.append('days_since_seen')
            fields.append('days_before_joined')


    data = dict()
    for f in fields:
        data[f] = []

    # FIXME: all this code should be cleaned up.

    totals = None
    if not by_author:
        if interval != 'LF':
            totals = Statistic.objects.select_related('repo',).filter(
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
            totals = Statistic.objects.select_related('repo','author').filter(
                interval=interval,
                repo=repo,
                author__pk__in=top,
                #start_date__range=(start, end)
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

    if interval != 'LF':
        totals = totals.order_by('author','start_date')
    else:
        totals = totals.order_by('author')

    first_day = repo.earliest_commit_date()

    for t in totals:
        for f in fields:
            if f == 'date':
                data[f].append(t.start_date)
                if first_day is None:
                    first_day = t.start_date
            elif f == 'day':
                day = (t.start_date - first_day).days
                # print("DAY=%s" % day)
                data[f].append(day)
            elif f == 'author':
                data[f].append(t.author.email)
            elif f == 'average_commit_size':
                data[f].append(int(float(t.lines_changed) / float(t.commit_total)))
            else:
                data[f].append(getattr(t, f))

    return pd.DataFrame(data, columns=fields)

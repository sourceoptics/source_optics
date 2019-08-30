import pandas as pd
from .. models import Statistic, Commit, Author
from django.db.models import Count, Sum

def get_interval(start, end):
    delta = end-start
    if delta.days > 365:
        return 'MN'
    else:
        return 'DY'

def get_top_authors(repo, start, end, attribute='commit_total', limit=10):

    interval = get_interval(start, end)

    authors = []
    filter_set = Statistic.objects.filter(
        interval=interval,
        author__isnull=False,
        repo=repo,
        start_date__range=(start, end)
    ).values('author_id').annotate(total=Sum(attribute)).order_by('-total')[0:limit]

    # FIXME: one query per author, somewhat slow
    for t in filter_set:
        top_auth = Author.objects.get(pk=t['author_id'])
        authors.append(top_auth)


    return authors

def total_series(repo, start=None, end=None):

    interval = get_interval(start, end)

    # FIXME: DRY

    data = dict()

    dates = []
    lines_changed = []
    commit_totals = []

    authors = get_top_authors(repo, start, end)
    authors_pk = [a.pk for a in authors]

    author = Commit.objects.filter(
        repo=repo
    ).values('author').distinct()

    totals = Statistic.objects.select_related('repo', 'author').filter(
        interval=interval,
        repo=repo,
        author__isnull=True,
        start_date__range=(start, end)
    ).order_by('start_date')

    for t in totals:
        dates.append(t.start_date)
        lines_changed.append(t.lines_changed)
        commit_totals.append(t.commit_total)

    results = dict(
        date=dates,
        commits=commit_totals,
        lines_changed=lines_changed
    )

    return pd.DataFrame(results, columns=['date', 'lines_changed', 'commits'])


def author_series(repo, start=None, end=None):

    interval = get_interval(start, end)

    #data = dict()

    dates = []
    lines_changed = []
    commit_totals = []
    emails = []


    authors = get_top_authors(repo, start, end)
    authors_pk = [ a.pk for a in authors ]

    #author = Commit.objects.filter(
    #    repo=repo
    #).values('author').distinct()

    totals = Statistic.objects.select_related('repo','author').filter(
        interval=interval,
        repo=repo,
        author__pk__in=authors_pk,
        start_date__range=(start, end)
    ).order_by('author','start_date')

    for t in totals:
        dates.append(t.start_date)
        lines_changed.append(t.lines_changed)
        commit_totals.append(t.commit_total)
        emails.append(t.author.email)


    results = dict(
        date = dates,
        author = emails,
        commits = commit_totals,
        lines_changed = lines_changed
    )

    return pd.DataFrame(results, columns=['date', 'lines_changed', 'commits', 'author'])



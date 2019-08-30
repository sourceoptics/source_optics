import pandas as pd
from .. models import Statistic, Commit, Author, Repository
from django.db.models import Count, Sum

def get_interval(start, end):
    # FIXME: this isn't quite a solid plan for educational vs corporate repos when people may want to zoom in.
    # it's good enough for now, but should probably evolve later to be web-configurable.
    delta = end-start
    if delta.days > 365:
        return 'MN'
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
            fields = [ 'date', 'lines_changed', 'commit_total', 'author_total' ]
        else:
            fields = [ 'date', 'author', 'lines_changed', 'commit_total', 'author_total' ]


    data = dict()
    for f in fields:
        data[f] = []


    if not by_author:
        totals = Statistic.objects.select_related('repo','author').filter(
            interval=interval,
            repo=repo,
            author__isnull=True,
            start_date__range=(start, end)
        )
    else:
        top = top_authors(repo, start, end)
        totals = Statistic.objects.select_related('repo','author').filter(
            interval=interval,
            repo=repo,
            author__pk__in=top,
            start_date__range=(start, end)
        )

    totals = totals.order_by('author','start_date')

    for t in totals:
        for f in fields:
            if f == 'date':
                data[f].append(t.start_date)
            elif f == 'author':
                data[f].append(t.author.email)
            else:
                data[f].append(getattr(t, f))


    return pd.DataFrame(data, columns=fields)

OLDER = """

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

def contributors_series(repo, start=None, end=None):
    # FIXME: return the number of contributors each month, possibly with seperate data for new vs returning
    interval = 'MN'
    return "FIXME"

def health_matrix(repo, start=None, end=None):

    repo = Repository.objects.get(pk=repo)


    repo_start = repo.earliest_commit_date()

    interval = get_interval(start, end)

    author_ids = repo.author_ids(start, end)
    authors = Author.objects.filter(pk__in=author_ids)

    print("AUTHORS=%s" % authors)


    earliest_commit_dates = []
    latest_commit_dates = []
    commit_counts = []
    lines_added = []
    lines_removed = []
    lines_changed = []
    days_before_joined = []
    days_since_seen = []
    files_changed = []
    average_commit_size = []
    emails = []

    for author in authors.all():

        # FIXME: we can do this more efficiently later

        earliest = author.earliest_commit_date(repo)
        latest = author.latest_commit_date(repo)
        since_seen = (latest-earliest).days
        since_start = (earliest-repo_start).days
        stats = author.statistics(repo, start, end, interval)

        if stats['lines_changed'] is None:
            # FIXME: not sure how this happens exactly, possibly a consequence of our file move bug
            # not yet being sorted out
            continue


        earliest_commit_dates.append(earliest)
        latest_commit_dates.append(latest)


        # print("Author, %s, %s" % (author, stats))
        lines_changed.append(stats['lines_changed'])
        lines_added.append(stats['lines_added'])
        lines_removed.append(stats['lines_removed'])
        commit_counts.append(stats['commit_total'])
        average_commit_size.append(int(float(stats['lines_changed']) / float(stats['commit_total'])))
        days_since_seen.append(since_seen)
        days_before_joined.append(since_start)
        emails.append(author.email)

    print(days_since_seen)
    print(days_before_joined)

    data = dict(
        earliest_commit = earliest_commit_dates,
        latest_commit = latest_commit_dates,
        lines_changed = lines_changed,
        lines_added = lines_added,
        commits = commit_counts,
        author = emails,
        days_since_seen = days_since_seen,
        days_before_joined = days_before_joined,
        average_commit_size = average_commit_size,
    )
    return pd.DataFrame(data,
                        columns=['lines_changed', 'lines_added',
                                 'commits', 'author', 'days_since_seen', 'days_before_joined', 'average_commit_size'])

   

    def _contributors_per_month(self, repo):
        print("stat...")
        commit_months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC')
        data = []
        for start_day in commit_months:
            # this is long, sorry
            data.append([start_day, Commit.objects.filter(repo=repo, commit_date__month=start_day.month, commit_date__year=start_day.year).values_list('author').distinct().count() ])
        return data


    def _commits_per_month(self, repo):
        print("stat...")
        commit_months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC')
        data = []
        for start_day in commit_months:
            data.append([start_day, Commit.objects.filter(repo=repo, commit_date__month=start_day.month, commit_date__year=start_day.year).count() ])
        return data

    def _changed_per_month(self, repo):
        print("stat...")
        commit_months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC')
        data = []
        for start_day in commit_months:
            stat = Statistic.objects.filter(repo=repo, author__isnull=True, start_date__month=start_day.month, start_date__year=start_day.year).first()
            if stat is not None:
                data.append([start_day, stat.lines_changed])
        return data

    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None):

        # author filter is ignored, guess that is ok for now


        data = dict()
        data['meta'] = dict(
            format = 'custom'
        )
        reports = data['reports'] = dict()


        for repo in repos:

            author_ids = Commit.objects.filter(repo=repo).values_list('author__pk', flat=True).distinct().all()
            authors = Author.objects.filter(pk__in=author_ids)

            repo_report = reports[repo.name] = dict()

            repo_report['earliest_vs_latest'] = self._earliest_vs_latest(repo=repo, authors=authors)
            repo_report['earliest_vs_commits'] = self._earliest_vs_commits(repo=repo, authors=authors)
            repo_report['earliest_vs_changed'] = self._earliest_vs_changed(repo=repo, authors=authors)
            repo_report['latest_vs_commits'] = self._latest_vs_commits(repo=repo, authors=authors)
            repo_report['latest_vs_changed'] = self._latest_vs_changed(repo=repo, authors=authors)
            repo_report['contributors_per_month'] = self._contributors_per_month(repo=repo)
            repo_report['commits_per_month'] = self._commits_per_month(repo=repo)
            repo_report['changed_per_month'] = self._changed_per_month(repo=repo)


        return data

"""
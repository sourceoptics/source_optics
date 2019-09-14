
import json
from source_optics.models import (Author, Statistic, Commit)
from django.core.paginator import Paginator

def commits_feed(scope): # repos=None, organization=None, repo=None, start=None, end=None, author_email=None, author_domain=None, page_size=50, page=0):

    # FIXME: looks like a function
    objs = None

    repo = scope.repo
    author = scope.author
    organization = scope.org
    start = scope.start
    end = scope.end
    author_email = scope.author_email
    author_domain = scope.author_domain
    #page = scope.page
    #page_size = scope.page_size

    if repo and author:
        objs = Commit.objects.filter(repo=repo, author=author)
    elif repo:
        objs = Commit.objects.filter(repo=repo)
    elif author:
        objs = Commit.objects.filter(author=author)
    elif organization:
        objs = Commit.objects.filter(repo__organization=organization)
    else:
        raise Exception("?")

    if start and end:
        objs = objs.filter(commit_date__range=(start,end))

    if author_email:
        objs = objs.filter(author__email=author_email)
    elif author_domain:
        objs = objs.filter(author__email__contains="@%s" % author_domain)

    # all this nested filtering apparently can make bad queries, so we should probably unroll all of the above?

    objs = objs.select_related('author').order_by('-commit_date')

    count = objs.count()

    results = []

    paginator = Paginator(objs, scope.page_size)
    page = paginator.page(scope.page)

    # we may wish to show filechange info here
    for commit in page:
        desc = commit.subject
        if desc is None:
            desc = ""
        desc = desc[:255]
        results.append(dict(
            repo=commit.repo.name,
            commit_date=str(commit.commit_date),
            author_id=commit.author.pk,
            author=commit.author.email,
            sha=commit.sha,
            subject=desc
        ))

    return dict(results=results, page=page, count=count)


def author_stats_table(scope, limit=None):
    """
    this drives the author tables, both ranged and non-ranged, accessed off the main repo list.
    the interval 'LF' shows lifetime stats, but elsewhere we just do daily roundups, so this parameter
    should really be a boolean.  The limit parameter is not yet used.
    """

    results = []


    interval = scope.interval
    if interval != 'LF':
        interval = 'DY'

    authors = None
    if scope.repo:
        authors = Author.authors(scope.repo, scope.start, scope.end)

    def add_stat(author, repo):
        stat1 = Statistic.queryset_for_range(repo, author=author, start=scope.start, end=scope.end, interval=scope.interval)
        stat2 = Statistic.compute_interval_statistic(stat1, interval=scope.interval, repo=repo, author=author, start=scope.start, end=scope.end)
        stat2 = stat2.to_dict()
        stat2['author'] = author.email
        stat2['repo'] = repo.name
        if stat2['lines_changed']:
            # skip authors with no contribution in the time range
            results.append(stat2)

    if not scope.author and scope.repo:
        for author in authors:
            add_stat(author, scope.repo)
    elif scope.author and not scope.repo:
        for repo in scope.author.repos():
            add_stat(scope.author, repo)
    elif scope.author and scope.repo:
        add_stat(scope.author, scope.repo)

    return results


def repo_table(scope): # repos, start, end):

    """
    this drives the list of all repos within an organization, showing the statistics for them within the selected
    time range, along with navigation links.
    """

    results = []
    for repo in scope.repos:
        stats = Statistic.queryset_for_range(repo, author=None, interval='DY', start=scope.start, end=scope.end)
        stat2 = Statistic.compute_interval_statistic(stats, interval='DY', repo=repo, author=None, start=scope.start, end=scope.end)
        stat2 = stat2.to_dict()
        stat2['name'] = repo.name
        if repo.last_scanned:
            stat2['last_scanned'] = repo.last_scanned.strftime("%Y-%m-%d %H:%M:%S")
        else:
            stat2['last_scanned'] = ""
        # providing pk's for link columns in the repo chart
        for x in [ 'details1', 'details2', 'details3']:
            stat2[x] = repo.pk
        results.append(stat2)
    results = sorted(results, key=lambda x: x['name'])
    return json.dumps(results)

def orgs_table(scope):

    results = []
    for org in scope.orgs:
        row = dict()
        row['name'] = org.name
        row['repo_count'] = org.repos.count()
        print("repo_count=%s" % row['repo_count'])
        row['details1'] = org.pk
        results.append(row)
    return json.dumps(results)
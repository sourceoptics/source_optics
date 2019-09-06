
import json
from source_optics.models import (Author, Statistic)

def commits_table(scope): # repos=None, organization=None, repo=None, start=None, end=None, author_email=None, author_domain=None, page_size=50, page=0):

    raise Exception("NOT IMPLEMENTED YET, WIP")

    # FIXME: looks like a function
    objs = None
    if repo and author:
        Commits.objects.filter(organization=organization, repo=repo, author=author)
    elif repo:
        Commits.objects.filter(organization=organization, repo=repo)
    elif author:
        Commits.objects.filter(organization=organization, author=author)
    else:
        Commits.objects.filter(organization==organization)

    if start and end:
        objs = Commit.objects.filter(commit__date__range=(start,end))

    if author_email:
        objs = objs.filter(author__email=author_email)
    elif author_domain:
        objs = objs.filter(author__email__contains="@%s" % author_domain)

    objs = objs.select_related('author','filechanges')

    count = objs.count()
    start_index = page * page_size
    end_index = start_index + page_size

    objs = objs[start_index:end_index]

    results = []

    # we may wish to show filechange info here
    for commit in objs:
        desc = commit.description
        if desc is None:
            desc = ""
        desc = desc[:255]
        results.append(dict(
            author_id=commit.author.pk,
            author=commit.author.email,
            sha=commit.sha,
            desc=desc
        ))

    return dict(results=results, count=count)


def author_table(scope, limit=None):
    """
    this drives the author tables, both ranged and non-ranged, accessed off the main repo list.
    the interval 'LF' shows lifetime stats, but elsewhere we just do daily roundups, so this parameter
    should really be a boolean.  The limit parameter is not yet used.
    """

    results = []

    interval = scope.interval
    if interval != 'LF':
        interval = 'DY'

    authors = Author.authors(scope.repo, scope.start, scope.end)

    for author in authors:
        stat1 = Statistic.queryset_for_range(scope.repo, author=author, start=scope.start, end=scope.end, interval=scope.interval)
        stat2 = Statistic.compute_interval_statistic(stat1, interval=scope.interval, repo=scope.repo, author=author, start=scope.start, end=scope.end)
        stat2 = stat2.to_dict()
        stat2['author'] = author.email
        if stat2['lines_changed']:
            # skip authors with no contribution in the time range
            results.append(stat2)
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
        # providing pk's for link columns in the repo chart
        for x in [ 'details1', 'details2', 'details3']:
            stat2[x] = repo.pk
        results.append(stat2)
    results = sorted(results, key=lambda x: x['name'])
    return json.dumps(results)

import json
from source_optics.models import (Repository, Statistic, Commit)
from django.db.models import Sum, Count, Max
from django.core.paginator import Paginator

def commits_feed(scope):

    objs = None

    repo = scope.repo
    author = scope.author
    organization = scope.org
    start = scope.start
    end = scope.end
    author = scope.author


    # FIXME: this looks like a method we should add to Scope() but only to be called when needed
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

    if author:
        objs = objs.filter(author__pk=author.pk)

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

def _annotations_to_table(stats, primary, lookup):

    results = []

    for entry in stats:
        new_item = {}
        new_item[primary] = entry[lookup]
        for (k,v) in entry.items():
            if k.startswith("annotated_"):
                k2 = k.replace("annotated_","")
                if 'date' in k2 or 'last_scanned' in k2:
                    new_item[k2] = str(v)
                else:
                    new_item[k2] = v
        # for making things easy with ag-grid, the primary key is available multiple times:
        for x in [ 'details1', 'details2', 'details3']:
            new_item[x] = entry[lookup]
        results.append(new_item)
    print(results)
    return results


def author_stats_table(scope, limit=None):
    """
    this drives the author tables, both ranged and non-ranged, accessed off the main repo list.
    the interval 'LF' shows lifetime stats, but elsewhere we just do daily roundups, so this parameter
    should really be a boolean.  The limit parameter is not yet used.
    """

    # FIXME: this performs one query PER author and could be rewritten to be a LOT more intelligent.

    (repos, authors) = scope.standardize_repos_and_authors()
    interval = 'DY'
    stats = Statistic.queryset_for_range(repos=repos, authors=authors, start=scope.start, end=scope.end, interval=interval)
    stats = Statistic.annotate(stats.values('author__email')).order_by('author__email')
    data = _annotations_to_table(stats, 'author', 'author__email')
    return data




def repo_table(scope): # repos, start, end):

    #this drives the list of all repos within an organization, showing the statistics for them within the selected
    #time range, along with navigation links.

    (repos, authors) = scope.standardize_repos_and_authors()
    interval = 'DY'
    # FIXME: explain
    repos = [ x.pk for x in scope.available_repos.all() ]
    print("IN REPOS=", repos)
    print("IN AUTHORS=", authors)
    stats = Statistic.queryset_for_range(repos=repos, authors=authors, start=scope.start, end=scope.end, interval=interval)
    stats = Statistic.annotate(stats.values('repo__name')).order_by('repo__name')
    print("COUNTED=%s" % stats.count())
    data = _annotations_to_table(stats, 'repo', 'repo__name')
    # some repos won't have been scanned, and this requires a second query to fill them into the table
    repos = Repository.objects.filter(last_scanned=None, organization=scope.org)
    for unscanned in repos:
        data.append(dict(
            repo=unscanned.name
        ))
    return data


def orgs_table(scope):

    results = []
    for org in scope.orgs:
        row = dict()
        row['name'] = org.name
        row['repo_count'] = org.repos.count()
        row['details1'] = org.pk
        results.append(row)
    return json.dumps(results)
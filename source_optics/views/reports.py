
import json
from source_optics.models import (Repository, Statistic, Commit, Author, File, FileChange)
from django.core.paginator import Paginator

def files(scope):
    # the files report view
    repo = scope.repo
    path = scope.path
    if path == '/':
        path = ''

    kids = get_child_paths(repo, path)
    files = get_files(repo, path)

    if path == "":
        path = "/"

    return dict(
        path=path,
        paths=kids,
        paths_length=len(kids),
        files=files,
        files_length=len(files)
    )

def get_child_paths(repo, path):

    # find all the directory paths
    all_paths = File.objects.filter(
        repo=repo,
        path__startswith=path,
    ).values_list('path', flat=True).distinct().all()

    slashes = path.count('/')
    desired = slashes

    # find all the paths that are one level deeper than the specified path
    # the removal of "=>" deals with moved path detection in old versions of the program w/ legacy data
    children = [ dict(path=path) for path in sorted(all_paths) if ((not '=>' in path) and (path.count('/') == desired)) ]

    return children

def get_files(repo, path):

    all_files = File.objects.filter(
        repo=repo,
        path=path,
    ).order_by('name').all()

    return [ dict(filename=f.name, path=f.path) for f in all_files.all() ]


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
            author_name=commit.author.display_name,
            sha=commit.sha,
            subject=desc
        ))

    return dict(results=results, page=page, count=count)

def _annotations_to_table(stats, primary, lookup):

    """
    Processes a list of statistics objects and converts annotated values
    from those statistics objects back to the field names used in the tables.
    """

    results = []

    for entry in stats:
        new_item = {}
        new_item[primary] = entry[lookup]
        for (k,v) in entry.items():
            if k.startswith("annotated_"):
                k2 = k.replace("annotated_","")
                if 'date' in k2 or 'last_scanned' in k2 or 'name' in k2:
                    new_item[k2] = str(v)
                else:
                    new_item[k2] = v
        # for making things easy with ag-grid, the primary key is available multiple times:
        for x in [ 'details1', 'details2', 'details3']:
            new_item[x] = entry[lookup]
        results.append(new_item)
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
    data = None
    if not scope.author:
        stats = Statistic.annotate(stats.values('author__email')).order_by('author__email')
        data = _annotations_to_table(stats, 'author', 'author__email')
    else:
        stats = Statistic.annotate(stats.values('repo__name')).order_by('repo__name')
        data = _annotations_to_table(stats, 'repo', 'repo__name')
    return data


# FIXME: see what's up with the author table


def repo_table(scope): # repos, start, end):

    #this drives the list of all repos within an organization, showing the statistics for them within the selected
    #time range, along with navigation links.

    (repos, authors) = scope.standardize_repos_and_authors()
    interval = 'DY'
    # FIXME: explain
    repos = [ x.pk for x in scope.available_repos.all() ]
    stats = Statistic.queryset_for_range(repos=repos, authors=authors, start=scope.start, end=scope.end, interval=interval)
    stats = Statistic.annotate(stats.values('repo__name')).order_by('repo__name')
    data = _annotations_to_table(stats, 'repo', 'repo__name')

    # FIXME: insert in author count, which is ... complicated ... this can be optimized later
    # we should be able to grab every repo and annotate it with the author count in one extra query tops
    # but it might require manually writing it.
    for d in data:
        repo = d['repo']
        author_count = Author.author_count(repo, start=scope.start, end=scope.end)
        d['author_count'] = author_count

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

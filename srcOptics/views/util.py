from django.http import *
from django.core import serializers
from datetime import datetime, timedelta
from django.db.models import Sum

from ..models import *

"""
Returns a JSON list of repositories by search query
"""
def search(request, q):
    repos = query(q)
    data = serializers.serialize('json',repos)
    return HttpResponse(data, content_type='application/json')

"""
Returns a list of Repository objects from filter query
"""
def query(q):
    repos = None
    if not q:
        repos = Repository.objects.all()
    else:
        repos = Repository.objects.filter(name__icontains=q)
        tag_query = Tag.objects.filter(name__icontains=q)
        for tag in tag_query:
            repos |= tag.repos.all()
    return repos

"""
Generate a dictionary with all the statistics for a given repository, given author,
and given date range
"""
def aggregate_stats(repo, author, start, end):

    # Get statistics objects in the appropriate interval
    days = Statistic.objects.filter(interval='DY', repo=repo, author=author, file=None, start_date__range=(start, end))

    # Calculate sums from statistics objects into an object
    totals = days.aggregate(lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"),
                    lines_changed=Sum("lines_changed"), commit_total=Sum("commit_total"),
                    files_changed=Sum("files_changed"), author_total=Sum("author_total"))

    # append to stats list
    totals['repo_last_scanned'] = repo.last_scanned
    totals['repo_last_pulled'] = repo.last_pulled

    totals['repo_tags'] = repo.tags.all()

    return totals

"""
Returns a list of Statistic objects from start / end date in
a given list of repositories
"""
def get_all_repo_stats(repos, author, start, end):
    # Loop through repos and add appropriate statistics to table
    stats = []
    for repo in repos:
        totals = aggregate_stats(repo, author, start, end)
        # Add repository name to totals object to display
        totals['repo'] = repo
        stats.append(totals)
    return stats

"""
Returns a list of Statistic objects for a list of authors in a
given time interval
"""
def get_all_author_stats(authors, repo, start, end):
    stats = []
    for author in authors:
        totals = aggregate_stats(repo, author, start, end)
        # Add repository name to totals object to display
        totals['author'] = author
        stats.append(totals)
    return stats

"""
Returns a start and end date from query strings or defaults to one week
"""
def get_date_range(request):
    # Get query strings
    start = request.GET.get('start')
    end = request.GET.get('end')

    # Sets default date range to a week if no query string is specified
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
    else:
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')
    return start, end

"""
Returns an array of the top 6 contributing authors
"""
def get_top_authors(repo, start, end, attribute):
    # Get every author with displayed repo; limit 5
    authors = []
    #First get all daily interval author stats within the range
    filter_set = Statistic.objects.filter(
        interval='DY',
        author__isnull=False,
        repo=repo,
        start_date__range=(start, end)
    )

    #Then aggregate the filter set based on the attribute, get top 5
    top_set = filter_set.annotate(total_attr=Sum(attribute)).order_by('-total_attr')

    #append top 5 authors to author set to display
    i = 0
    for t in top_set:
        if t.author not in authors and i < 6:
            authors.append(t.author)
            i += 1

    return authors

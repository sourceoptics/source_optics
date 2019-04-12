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
Returns a list of Statistic objects from start / end date in
a given list of repositories
"""
def get_stats(repos, start, end):
    # Loop through repos and add appropriate statistics to table
    stats = []
    for repo in repos:
        # Get statistics objects in the appropriate interval
        days = Statistic.objects.filter(interval='DY', repo=repo, author=None, file=None, start_date__range=(start, end))

        # Calculate sums from statistics objects into an object
        totals = days.aggregate(lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"),
                        lines_changed=Sum("lines_changed"), commit_total=Sum("commit_total"),
                        files_changed=Sum("files_changed"), author_total=Sum("author_total"))

        # Add repository name to object and append to stats list
        totals['repo'] = repo
        totals['repo_last_scanned'] = repo.last_scanned
        totals['repo_last_pulled'] = repo.last_pulled

        totals['repo_tags'] = repo.tags.all()
        #print("TAGS " , totals['repo_tags'])
        stats.append(totals)
    return stats


def get_query_strings(request):
    queries = {}

    start = request.GET.get('start')
    end = request.GET.get('end')

    # Sets default date range to a week if no query string is specified
    if not start or not end:
        queries['end'] = datetime.now()
        queries['start'] = queries['end'] - timedelta(days=7)
    else:
        queries['start'] = datetime.strptime(start, '%Y-%m-%d')
        queries['end'] = datetime.strptime(end, '%Y-%m-%d')

    attribute = request.GET.get('attr')
    if not attribute:
        queries['attribute'] = Statistic.ATTRIBUTES[0][0]
    else:
        queries['attribute'] = request.GET.get('attr')

    interval = request.GET.get('intr')
    if not interval:
        queries['interval'] = Statistic.INTERVALS[0][0]
    else:
        queries['interval'] = request.GET.get('intr')
    

    return queries

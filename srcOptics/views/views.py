from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig
from django.db.models import Sum
from datetime import datetime, timedelta

from ..models import *
from .tables import *

from random import randint

"""
View function for home page of site
"""
def index(request):

    # Get query strings
    start = request.GET.get('start')
    end = request.GET.get('end')
    search = request.GET.get('filter')

    repos = None
    if not search:
        repos = Repository.objects.all()
    else:
        repos = Repository.objects.filter(name__icontains=search)
        tag_query = Tag.objects.filter(name__icontains=search)
        for tag in tag_query:
            repos |= tag.repos.all()

    # Sets default date range to a week if no query string is specified
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
    else:
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')


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
        stats.append(totals)

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    context = {
        'title': 'SrcOptics',
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)


def repo_details(request, slug):
    repo = Repository.objects.get(name=slug)
    repos = [repo]
    start = request.GET.get('start')
    end = request.GET.get('end')
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
    else:
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')
    days = Statistic.objects.filter(interval='DY', repo=repo, author = None, file = None, start_date__range=(start, end))
    stats = days.aggregate(lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"),
                        lines_changed=Sum("lines_changed"), commit_total=Sum("commit_total"),
                        files_changed=Sum("files_changed"), author_total=Sum("author_total"))
    stats['repo'] = repo
    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)
    context = {
        'title': repo,
        'repositories': repo,
        'stats': stat_table
    }

    return render(request, 'repo_details.html', context=context)

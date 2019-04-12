from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig
from django.db.models import Sum
from datetime import datetime, timedelta
from django.utils import timezone

from . import graph, util

from .forms import RepositoryForm
from ..models import *
from .tables import *
from ..create import Creator

from random import randint

"""
View function for home page of site
"""
def index(request):
    #Passes the filter to util query to get a list of repos
    repos = util.query(request.GET.get('filter'))
    #Returns a start and end date from query strings
    start, end = util.get_date_range(request)
    #Aggregates statistics for a repository based on start and end date
    stats = util.get_stats(repos, start, end)
    #Returns statistic table data
    stat_table = StatTable(stats)

    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    context = {
        'title': 'SrcOptics',
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)


"""
Data to be displayed for the repo details view
"""
def repo_details(request, slug):
    #Gets repo name from url slug
    repo = Repository.objects.get(name=slug)

    start, end = util.get_date_range(request)

    stats = util.get_stats([repo], start, end)

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    #Generates line graphs based on attribute query param
    line_elements = graph.attribute_graphs(request, slug)

    #Generates line graph of an attribute for the top 5 Contributors
    # to that attribute within the specified time period
    author_elements = graph.attribute_author_graphs(request, slug)

    #possible attribute values to filter by
    attributes = Statistic.ATTRIBUTES

    #possible interval values to filter by
    intervals = Statistic.INTERVALS

    #Summary Statistics

    lifetime = Statistic.objects.filter(interval='MN', repo=repo,
                                        author=None, file=None,
                                        start_date__range=(repo.earliest_commit, datetime.now(tz=timezone.utc)))


    summary_stats = lifetime.aggregate(commits=Sum("commit_total"), authors=Sum("author_total"),
                                       lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"),
                                       lines_changed=Sum("lines_changed"))



    #Context variable being passed to template
    context = {
        'title': "Repository Details: " + str(repo),
        'stats': stat_table,
        'summary_stats': summary_stats,
        'data': line_elements,
        'author_data': author_elements,
        'attributes': attributes,
        'intervals':intervals
    }
    return render(request, 'repo_details.html', context=context)

# Renders the add repository page, must retrieve the organizations and credentials
# in the database.
def add_repo(request):
    if request.method == 'POST':
        form = RepositoryForm(request.POST)
        if form.is_valid():
            fields = form.cleaned_data
            repo = Creator.create_repo(org_name=fields['organization'].name, cred=fields['credential'], repo_url=fields['url'], repo_name=fields['name'])
            repo.save()
            return HttpResponseRedirect('/complete/')

    else:
        form = RepositoryForm()

    return render(request, 'add_repo.html', {'form': form})

def attributes_by_repo(request):
    data = graph.attributes_by_repo(request)
    context = {
        'title': 'Repo Statistics Over Time',
        'data' : data,
        'attributes': Statistic.ATTRIBUTES,
        'intervals': Statistic.INTERVALS
    }
    return render(request, 'repo_view.html', context=context)

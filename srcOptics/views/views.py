from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig
from django.db.models import Sum
from datetime import datetime, timedelta
from django.utils import timezone

import decimal

from . import graph, util

from .forms import RepositoryForm
from ..models import *
from .tables import *
from ..create import Creator
from django.contrib.humanize.templatetags.humanize import intcomma

from random import randint

"""
View function for home page of site
"""
def index(request):
    #list of all organizations

    #organization parameter
    org = request.GET.get('org')

    #Passes the filter to util query to get a list of repos
    repos = util.query(request.GET.get('filter'), org)

    #Returns a start and end date from query strings
    queries = util.get_query_strings(request)

    #Aggregates statistics for a repository based on start and end date
    stats = util.get_all_repo_stats(repos=repos, start=queries['start'], end=queries['end'])
    #Returns statistic table data
    stat_table = StatTable(stats)


    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    context = {
        'title': 'SrcOptics',
        'organizations':Organization.objects.all(),
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

    queries = util.get_query_strings(request)

    stats = util.get_all_repo_stats(repos=[repo], start=queries['start'], end=queries['end'])

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    #Generates line graphs based on attribute query param
    line_elements = graph.attribute_graphs(request, slug)

    #Generates line graph of an attribute for the top contributors
    # to that attribute within the specified time period
    author_elements = graph.attribute_author_graphs(request, slug)

    #possible attribute values to filter by
    attributes = Statistic.ATTRIBUTES

    #possible interval values to filter by
    intervals = Statistic.INTERVALS

    # Get the attribute to get the top authors for from the query parameter
    attribute = request.GET.get('attr')

    if not attribute:
        attribute = attributes[0][0]

    # Generate a table of the top contributors statistics
    authors = util.get_top_authors(repo=repo, start=queries['start'], end=queries['end'], attribute=queries['attribute'])
    author_stats = util.get_all_author_stats(authors=authors, repo=repo, start=queries['start'], end=queries['end'])
    author_table = AuthorStatTable(author_stats)
    RequestConfig(request, paginate={'per_page': 6}).configure(author_table)

    summary_stats = util.get_lifetime_stats(repo)

    #Context variable being passed to template
    context = {
        'title': repo,
        'stats': stat_table,
        'summary_stats': summary_stats,
        'data': line_elements,
        'author_graphs': author_elements,
        'author_table': author_table,
        'attributes': attributes,
        'intervals':intervals
    }
    return render(request, 'repo_details.html', context=context)


"""
Data to be displayed for the author details view
"""
def author_details(request, slug):
    #Gets repo name from url slug
    auth = Author.objects.get(email=slug)

    queries = util.get_query_strings(request)

    stats = util.get_total_author_stats(author=auth, start=queries['start'], end=queries['end'])

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 5}).configure(stat_table)

    #Generates line graphs based on attribute query param
    line_elements = graph.attribute_summary_graph_author(request, auth)

    # get the top repositories the author commits to
    author_elements = graph.attribute_author_contributions(request, auth)

    #possible attribute values to filter by
    attributes = Statistic.ATTRIBUTES

    #possible interval values to filter by
    intervals = Statistic.INTERVALS

    # Get the attribute to get the top authors for from the query parameter
    attribute = request.GET.get('attr')

    if not attribute:
        attribute = attributes[0][0]

    # Generate a table of the top contributors statistics
    #authors = util.get_top_authors(repo=repo, start=queries['start'], end=queries['end'], attribute=queries['attribute'])
    #author_stats = util.get_all_author_stats(authors=authors, repo=repo, start=queries['start'], end=queries['end'])
    #author_table = AuthorStatTable(author_stats)
    #RequestConfig(request, paginate={'per_page': 10}).configure(author_table)

    summary_stats = util.get_lifetime_stats_author(auth)

    #Context variable being passed to template
    context = {
        'title': "Author Details: " + str(auth),
        'stats': stat_table,
        'summary_stats': summary_stats,
        'data': line_elements,
        'author_graphs': author_elements,
        'attributes': attributes,
        'intervals':intervals
    }
    return render(request, 'author_details.html', context=context)


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
        'organizations': Organization.objects.all(),
        'data' : data,
        'attributes': Statistic.ATTRIBUTES,
        'intervals': Statistic.INTERVALS,
        'repos': Repository.objects.all()
    }
    return render(request, 'repo_view.html', context=context)

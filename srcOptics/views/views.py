from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig
from django.db.models import Sum
from datetime import datetime, timedelta
from . import graph, util

from ..models import *
from .tables import *

from random import randint

"""
View function for home page of site
"""
def index(request):

    repos = util.query(request)

    start, end = util.get_date_range(request)


    # Loop through repos and add appropriate statistics to table
    stats = util.get_stats(repos, start, end)

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
    
    start, end = util.get_date_range(request)

    stats = util.get_stats([repo], start, end)

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    line_elements, attributes = graph.attribute_graphs(request, slug)

    context = {
        'title': repo,
        'repository': [repo],
        'stats': stat_table,
        'data': line_elements,
        'attribute': attributes
    }
    return render(request, 'repo_details.html', context=context)

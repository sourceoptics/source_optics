from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig
from datetime import datetime


from ..models import Repository, Commit, Statistic
from .tables import *

from random import randint

"""
View function for home page of site
"""
def index(request):
    repos = Repository.objects.all()
    start = request.GET.get('s')
    end = request.GET.get('e')
    if start and end:
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')
        duration = (end - start).days
        if duration > 7:
            stats = Statistic.objects.filter(interval='MN', start_date__gte=start)
        else:
            stats = Statistic.objects.filter(interval='WK', start_date__gte=start)
        # stats = Statistic.objects.filter(interval=filter_by_repo)
    else:
        stats = Statistic.objects.all()
    samples = []
    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)
    context = {
        'title': 'SrcOptics',
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)

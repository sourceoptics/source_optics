from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig
from django.db.models import Sum
from datetime import datetime, timedelta


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
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
    else:
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')
    stats = []
    for repo in repos:
        days = Statistic.objects.filter(interval='DY', repo=repo, author=None, file=None, start_date__range=(start, end))
        days = days.aggregate(lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"),
                        lines_changed=Sum("lines_changed"), commit_total=Sum("commit_total"),
                        files_changed=Sum("files_changed"), author_total=Sum("author_total"))
        days['repo'] = repo
        stats.append(days)
    samples = []
    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)
    context = {
        'title': 'SrcOptics',
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)

from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig


from ..models import Repository, Commit, Statistic
from .tables import *

from random import randint

"""
View function for home page of site
"""
def index(request):
    repos = Repository.objects.all()
    filter_by_repo = request.GET.get('repo')
    if filter_by_repo:
        stats = Statistic.objects.filter(repo__name=filter_by_repo)
    else:
        stats = Statistic.objects.all()
    samples = []
    for repo in repos:
        samples.append(Statistic(repo=repo, data={
        'lines_added': randint(50,500),
        'lines_removed': randint(50,500),
        'lines_changed': randint(50,500),
        'commit_total': randint(500,5000),
        'files_changed': randint(50,500),
        'author_total': randint(1,30)
    }))
    stat_table = StatTable(samples)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)
    context = {
        'title': 'SrcOptics',
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)

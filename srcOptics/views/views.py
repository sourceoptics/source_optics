from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig


from ..models import Repository, Commit, Statistic
from .tables import *

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
    data = {
        'lines_added': 12,
        'lines_removed': 3,
        'lines_changed': 23,
        'commit_total': 128,
        'files_changed': 23,
        'author_total': 2
    }
    sample = Statistic(data=data)
    #print(stats)
    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)
    context = {
        'title': 'SrcOptics',
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)

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
    date = request.GET.get('date')
    if date:
        print(date)
        # stats = Statistic.objects.filter(interval=filter_by_repo)
    else:
        stats = Statistic.objects.all()
    samples = []
    print(stats)
    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)
    context = {
        'title': 'SrcOptics',
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)

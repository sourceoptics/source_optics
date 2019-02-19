from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig


from ..models import Repository, Commit
from .tables import *

"""
Returns commit data for selected repository
"""
def repo_selected(request):
    if request.method == 'GET':
        slugs = request.get_full_path().split('/')

        select = slugs[slugs.index('repo') + 1]
        if select:
            commits = Commit.objects.filter(repo__name=select)
            context = {
                'commits': commits
            }
            return render(request, 'dashboard.html', context=context)
        else:
            return HttpResponseBadRequest('<h1>Bad request</h1>')

"""
View function for home page of site
"""
def index(request):
    repos = Repository.objects.all()
    table = CommitTable(Commit.objects.all())
    RequestConfig(request, paginate={'per_page': 10}).configure(table)
    context = {
        'title': 'SrcOptics',
        'stylesheet': 'main.css',
        'repositories': repos,
        'commits': table
    }

    # if request.method == 'GET':
    #     slugs = request.get_full_path().split('/')
    #     select = slugs[slugs.index('repo') + 1]
    #     if select:
    #         context['commits'] = Commit.objects.filter(repo__name=select)
    #     else:
    #         return HttpResponseBadRequest('<h1>Bad request</h1>')

    return render(request, 'dashboard.html', context=context)

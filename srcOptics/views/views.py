from django.shortcuts import render
from django.template import loader
from django.http import *


from ..models import Repository, Commit

"""
Returns commit data for selected repository
"""
def repo_selected(request):
    if request.method == 'GET':
        select = request.GET.get('id', None)
        if select:
            commits = Commit.objects.filter(repo__name=select)
            context = {
                'commits': commits
            }
            # print(commits)
            return render(request, 'commit_table.html', context=context)
        else:
            return HttpResponseBadRequest('<h1>Bad request</h1>')

"""
View function for home page of site
"""
def index(request):
    repos = Repository.objects.all()

    context = {
        'title': 'SrcOptics',
        'stylesheet': 'main.css',
        'repositories': repos

    }
    return render(request, 'dashboard.html', context=context)

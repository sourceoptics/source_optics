from django.shortcuts import render
from django.template import loader

from ..models import Repository, Commit

"""
Returns data for selected repository
"""
def repo_selected(request):
    if request.method == 'GET':
        select = request.GET.get('repo', None)
        print(select)
        if select:
            commits = Commit.objects.filter(repo__name=select)
            return commits
        else:
            return None

"""
View function for home page of site
"""
def index(request):
    repos = Repository.objects.all()
    commits = repo_selected(request)
    print(commits)

    context = {
        'title': 'SrcOptics',
        'stylesheet': 'main.css',
        'repositories': repos,
        'commits': commits

    }
    return render(request, 'dashboard.html', context=context)

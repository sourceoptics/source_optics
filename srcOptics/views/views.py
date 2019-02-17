from django.shortcuts import render
from django.template import loader

from ..models import Repository

"""
Returns data for selected repository
"""
def repo_selected(request):
    if request.method == 'GET':
        select = request.GET.get('id', None) 
        if select:
            repo = Commit.objects.filter(pk=selection)
            return repo
        else:
            return  #anything you want to send when no id value is sent in the ajax call

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

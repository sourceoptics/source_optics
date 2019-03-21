from django.shortcuts import render
from django.template import loader
from django.http import *
from django_tables2 import RequestConfig
from datetime import datetime


from ..models import Repository, Commit, Statistic
from .tables import *

from random import randint

import plotly.graph_objs as go
import plotly.offline as opy

graph_color = 'rgba(100, 50, 125, 1.0)'

"""
View basic graph for a repo
"""
def commits_by_repo(request):
    repos = Repository.objects.all()
    commits = []
    names = []

    for r in repos:
        names.append(r.name)
        count = Commit.objects.filter(repo=r).count()
        commits.append(count)

    # use plotly to make the graph
    # its html will be added to the data field of the context
    trace = go.Bar(
        x=names,
        y=commits,
        marker=dict(color=graph_color,line=dict(color=graph_color,width=1)),
        name='commits',
        orientation='v',
    )
    layout = go.Layout(title="Commits per Repository", xaxis={'title':'repository name'}, yaxis={'title':'commits'})
    fig = go.Figure(data=[trace],layout=layout)
    # save to a div element
    element = opy.plot(fig, auto_open=False, output_type='div')

    context = {
        'title': "Commits by repo",
        'data' : element
    }
    return render(request, 'repo_view.html', context=context)

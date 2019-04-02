from django.shortcuts import render
from django.template import loader

from django.http import *
from django_tables2 import RequestConfig

from ..models import Repository, Commit, Statistic, Tag, Author
from .tables import *

from . import util

from random import randint

from plotly import tools
import plotly.graph_objs as go
import plotly.offline as opy

GRAPH_COLORS = [
    'rgba(100, 50, 125, 1.0)',
    'rgba(100, 50, 0, 1.0)',
    'rgba(100, 50, 0, 1.0)',
    'rgba(100, 50, 0, 1.0)',
    'rgba(100, 50, 0, 1.0)',
]


"""
View basic graph for a repo
"""

# Uses the provided parameters to generate a graph and returns it
def generate_graph_data(**kwargs):
    # Array for dates
    dates = []

    # Array for attribute values
    attribute_by_date = []

    # Filter Rollup table for daily interval statistics for the current repository over the specified time range
    stats_set = Statistic.objects.filter(
        interval='DY', 
        repo=kwargs['repo'], 
        author=kwargs.get('author'), 
        start_date__range=(kwargs['start'], kwargs['end'])
    )

    # Adds dates and attribute values to their appropriate arrays to render into graph data
    for stat in stats_set:
        dates.append(stat.start_date)
        attribute_by_date.append(getattr(stat, kwargs['attribute']))

    # Creates a scatter plot for each element

    # Create traces
    trace0 = go.Scatter(
        x=dates,
        y=attribute_by_date,
        mode='lines+markers',
        name=kwargs['repo'].name,
        marker={
            'size': 10, 
            'line': {
                'width': 1
            },
            'color': GRAPH_COLORS[kwargs['row']-1]
        },
    )

    fig = kwargs.get('figure')
    if fig:
        fig.append_trace(trace0, kwargs['row'], 1)
        return fig
    else:
        return go.Figure(data=[trace0])

def attributes_by_repo(request):

    # List of possible attribute values to filter by. Defined in models.py for Statistic object
    attributes = Statistic.ATTRIBUTES

    # Attribute query parameter
    attribute = request.GET.get('attr')
    
    # Default attribute(total commits) if no query string is specified
    if not attribute:
        attribute = Statistic.ATTRIBUTES[0][0]
    
    # Query for repos based on the request (filter)
    repos = util.query(request)

    # Get start and end date for date range
    start, end = util.get_date_range(request)
    
    figure = tools.make_subplots(
        rows=len(repos),
        cols=1
    )
    # Iterate over repo queryset, generating attribute graph for each
    for i in range(len(repos)):
        figure = generate_graph_data(
            figure=figure,
            repo=repos[i],
            start=start,
            end=end,
            attribute=attribute,
            row=i+1,
        )
    
    figure['layout'].update(title='test')

    graph = opy.plot(figure, auto_open=False, output_type='div')

    context = {
        'title': "Repo Statistics Over Time",
        'data' : graph,
        'attributes': attributes
    }
    return render(request, 'repo_view.html', context=context)


def attribute_graphs(request, slug):
    # Attribute query parameter
    attribute = request.GET.get('attr')
    # Default attribute(total commits) if no query string is specified
    if not attribute:
        attribute = Statistic.ATTRIBUTES[0][0]

    # Get the repo object for the selected repository
    repo = Repository.objects.get(name=slug)

    # Get start and end date of date range
    start, end = util.get_date_range(request)

    # Generate a graph for displayed repository based on selected attribute
    figure = generate_graph_data(repo=repo, start=start, end=end, attribute=attribute, row=1)

    figure['layout'].update(title='test')

    graph = opy.plot(figure, auto_open=False, output_type='div')

    return graph

def attribute_author_graphs(request, slug):
    # Attribute query parameter
    attribute = request.GET.get('attr')

    # Default attribute(total commits) if no query string is specified
    if not attribute:
        attribute = Statistic.ATTRIBUTES[0][0]

    # Get the repo object for the selected repository
    repo = Repository.objects.get(name=slug)

    # Get start and end date of date range
    start, end = util.get_date_range(request)

    # Get every author with displayed repo; limit 5
    # TODO: Limit by top contributors
    authors = Author.objects.filter(repos__in=[repo])[:5]

    # Generate a graph for each author based on selected attribute for the displayed repo
    figure = tools.make_subplots(
        rows=len(authors),
        cols=1
    )
    for i in range(len(authors)):
        figure = generate_graph_data(
            figure=figure,
            repo=repo,
            start=start,
            end=end,
            author=authors[i],
            attribute=attribute,
            row=i+1
        )
    figure['layout'].update(height=600, title='Contributor Graphs')

    graph = opy.plot(figure, auto_open=False, output_type='div')

    return graph

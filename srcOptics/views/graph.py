from django.shortcuts import render
from django.template import loader

from django.db.models import Sum, Count

from django.http import *
from django_tables2 import RequestConfig

from ..models import Repository, Commit, Statistic, Tag, Author

from . import util

from .graphs.authors import AuthorGraph
from .graphs.repositories import RepositoryGraph

from plotly import tools
import plotly.graph_objs as go
import plotly.offline as opy
import math

GRAPH_COLORS = (
    '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#000000'
)


"""
View basic graph for a repo
"""

# Uses the provided parameters to generate a graph and returns it
def generate_graph_data(**kwargs):
    # Array for dates
    dates = []

    # Array for attribute values
    attribute_by_date = []
    author = kwargs.get('author')
    interval = kwargs.get('interval')

    # Filter Rollup table for daily interval statistics for the current repository over the specified time range
    stats_set = Statistic.objects.filter(
        interval=interval,
        repo=kwargs['repo'],
        author=author,
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
        mode='lines',
        name=kwargs['name'],
        fill='tonexty',
        line={
            'color': GRAPH_COLORS[hash(kwargs['name']) % len(GRAPH_COLORS)]
        },
        showlegend=False
    )

    fig = kwargs.get('figure')
    if fig:
        fig.append_trace(trace0, kwargs['row'], kwargs['col'])
        return fig
    else:
        return go.Figure(data=[trace0])

def attributes_by_repo(request):

    # Query for repos based on the request (filter)
    repos = util.query(request.GET.get('filter'))

    # Get start and end date for date range
    queries = util.get_query_strings(request)

    graph = RepositoryGraph(attribute=queries['attribute'], interval=queries['interval'], start=queries['start'], end=queries['end'], repos=repos).attributes_by_repo()

    return graph


"""
Generates an attribute line graph based on attribute query parameters
and start and end date
"""
def attribute_graphs(request, slug):

    # Get the repo object for the selected repository
    repo = Repository.objects.get(name=slug)

    # Get start and end date of date range
    queries = util.get_query_strings(request)

    # Generate a graph for displayed repository based on selected attribute
    figure = generate_graph_data(repo=repo, interval=queries['interval'], name=repo.name, start=queries['start'], end=queries['end'], attribute=queries['attribute'], row=1, col=1)

    figure['layout'].update(title=slug)

    graph = opy.plot(figure, auto_open=False, output_type='div')

    return graph

def attribute_author_graphs(request, slug):
    # Get the repo object for the selected repository
    repo = Repository.objects.get(name=slug)

    # Get start and end date of date range
    queries = util.get_query_strings(request)

    graph = AuthorGraph(attribute=queries['attribute'], interval=queries['interval'], start=queries['start'], end=queries['end'], repo=repo).top_graphs()
    return graph

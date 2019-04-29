from django.shortcuts import render
from django.template import loader

from django.db.models import Sum, Count

from django.http import *
from django_tables2 import RequestConfig

from ..models import Repository, Commit, Statistic, Tag, Author

from . import util

from .graphs.authors import *
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
    #
    # In the authors page, we leave out the repo argument
    if 'repo' in kwargs.keys():
        stats_set = Statistic.objects.filter(
            interval=interval,
            repo=kwargs['repo'],
            author=author,
            start_date__range=(util.get_first_day(kwargs['start'], interval), kwargs['end'])
        ).order_by('start_date')
    else:
        stats_set = Statistic.objects.filter(
            interval=interval,
            author=author,
            start_date__range=(util.get_first_day(kwargs['start'], interval), kwargs['end'])
        ).order_by('start_date')

    # sort the dates first so we don't add artifacts to the graph
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

    org = request.GET.get('org')
    # Query for repos based on the request (filter)
    repos = util.query(request.GET.get('filter'), org)

    # Get start and end date for date range
    queries = util.get_query_strings(request)

    graph = RepositoryGraph(q=queries, repos=repos).attributes_by_repo()

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

    graph = AuthorGraph(q=queries, repo=repo).top_graphs()
    return graph

def attribute_author_contributions(request, author):

    # Get start and end date of date range
    queries = util.get_query_strings(request)

    graph = AuthorContributeGraph(author=author, attribute=queries['attribute'],
                                  interval=queries['interval'], start=queries['start'],
                                  end=queries['end']).top_graphs()

    return graph

"""
Generates a line graph for an author details page
"""
def attribute_summary_graph_author(request, author):

    # Get start and end date of date range
    queries = util.get_query_strings(request)

    # Generate a graph for displayed repository based on selected attribute
    figure = generate_graph_data(author=author, interval=queries['interval'], name=author.email,
                                 start=queries['start'], end=queries['end'], attribute=queries['attribute'],
                                 row=1, col=1)

    figure['layout'].update(title=author.email)

    graph = opy.plot(figure, auto_open=False, output_type='div')

    return graph

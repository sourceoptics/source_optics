from django.shortcuts import render
from django.template import loader

from django.db.models import Sum, Count

from django.http import *
from django_tables2 import RequestConfig

from ..models import Repository, Commit, Statistic, Tag, Author
from .tables import *

from . import util

from random import randint

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

    # Filter Rollup table for daily interval statistics for the current repository over the specified time range
    stats_set = Statistic.objects.filter(
        interval='DY',
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

    )

    fig = kwargs.get('figure')
    if fig:
        fig.append_trace(trace0, kwargs['row'], kwargs['col'])
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
    repos = util.query(request.GET.get('filter'))

    # Get start and end date for date range
    start, end = util.get_date_range(request)

    figure = tools.make_subplots(
        rows=len(repos),
        cols=1,
        shared_xaxes=True,
        shared_yaxes=True,
        vertical_spacing=0.1,
        subplot_titles=tuple([_.name for _ in repos]),
    )
    # Iterate over repo queryset, generating attribute graph for each
    for i in range(len(repos)):
        figure = generate_graph_data(
            figure=figure,
            repo=repos[i],
            name=repos[i].name,
            start=start,
            end=end,
            attribute=attribute,
            row=i+1,
            col=1
        )
    figure['layout'].update(height=800)

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
    figure = generate_graph_data(repo=repo, name=repo.name, start=start, end=end, attribute=attribute, row=1, col=1)

    figure['layout'].update(title=slug)

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
    #authors = Author.objects.filter(repos__in=[repo])[:5]
    authors = []
    #First get all daily interval author stats within the range
    filter_set = Statistic.objects.filter(
        interval='DY',
        author__isnull=False,
        repo=repo,
        start_date__range=(start, end)
    )

    #Then aggregate the filter set based on the attribute, get top 5
    top_set = filter_set.annotate(total_attr=Sum(attribute)).order_by('-total_attr')

    #append top 5 authors to author set to display
    i = 0
    for t in top_set:
        if t.author not in authors and i < 5:
        #    print(getattr(t, attribute))
            authors.append(t.author)
            i += 1




    # Generate a graph for each author based on selected attribute for the displayed repo
    figure = tools.make_subplots(
        rows=math.ceil(len(authors)/2),
        cols=2,
        shared_xaxes=True,
        vertical_spacing=0.1,
        shared_yaxes=True,
        subplot_titles=tuple([_.email for _ in authors]),
    )
    for i in range(len(authors)):
        figure = generate_graph_data(
            figure=figure,
            repo=repo,
            name=authors[i].email,
            start=start,
            end=end,
            author=authors[i],
            attribute=attribute,
            row=math.floor(i/2) + 1,
            col=( i % 2 )+1

        )
    figure['layout'].update(height=800,title='Contributor Graphs')

    graph = opy.plot(figure, auto_open=False, output_type='div')

    return graph

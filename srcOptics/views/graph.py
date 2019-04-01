from django.shortcuts import render
from django.template import loader

from django.http import *
from django_tables2 import RequestConfig

from ..models import Repository, Commit, Statistic, Tag, Author
from .tables import *

from . import util

from random import randint

import plotly.graph_objs as go
import plotly.offline as opy

GRAPH_COLOR = 'rgba(100, 50, 125, 1.0)'

"""
View basic graph for a repo
"""

"""
Creates bar graph and returns bar graph element
"""
def create_bar_graph(**kwargs):
    # use plotly to make the graph
    # its html will be added to the data field of the context
    trace = go.Bar(
        x=kwargs['x_axis_data'],
        y=kwargs['y_axis_data'],
        marker={
            'color': GRAPH_COLOR,
            'line': {
                'color': GRAPH_COLOR,
                'width': 1
            }
        }
        ,
        name='Commits',
        orientation='v',
    )
    layout = go.Layout(
        title=kwargs['title'],
        margin={
            # 'l':50,
            # 'r':50,
            # 'b':100,
            # 't':100,
            # 'pad':20
        },
        xaxis={
            'title': kwargs['x_axis_title'],
            'tickfont': {
                'color': '#696969',
                'size': 18,
            }
        },
        yaxis={
            'title': kwargs['y_axis_title'],
            'tickfont': {
                'color': '#696969',
                'size': 18,
            }
        },
        font={'family': 'Lato, san-serif'},
        # width=1060,
        # height=600
    )
    fig = go.Figure(data=[trace],layout=layout)
    # save to a div element
    element = opy.plot(fig, auto_open=False, output_type='div')
    return element

"""
Creates and returns the HTML for a scatter plot.
"""
def create_scatter_plot(**kwargs):
    # Create traces
    trace0 = go.Scatter(
        x=kwargs['x_axis_data'],
        y=kwargs['y_axis_data'],
        mode='lines+markers',
        name='lines+markers',
        marker={
            'size': 14, 
            'line': {
                'width':1
            },
            'color': GRAPH_COLOR
        },
    )

    layout = go.Layout(
        title=kwargs['title'],
        xaxis={
            'title': kwargs['x_axis_title'],
        },
        yaxis={
            'title': kwargs['y_axis_title'],
        },
    )
    fig = go.Figure(data = [trace0], layout=layout)
    element = opy.plot(fig, auto_open=False, output_type='div')
    return element

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
    line_element = create_scatter_plot(
        title=kwargs['repo'].name, 
        x_axis_title='Date', 
        y_axis_title=kwargs['attribute'].replace("_", " ").title(), 
        x_axis_data=dates,
        y_axis_data=attribute_by_date
    )
    return line_element

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
    
    line_elements = ""
    # Iterate over repo queryset, generating attribute graph for each
    for repo in repos:
        line_element = generate_graph_data(repo=repo, start=start, end=end, attribute=attribute)
        line_elements += line_element

    context = {
        'title': "Repo Statistics Over Time",
        'data' : line_elements,
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
    repo = Repository.objects.get(name = slug)

    # Get start and end date of date range
    start, end = util.get_date_range(request)

    # Generate a graph for displayed repository based on selected attribute
    line_elements = ""
    line_element = generate_graph_data(repo=repo, start=start, end=end, attribute=attribute)
    line_elements += line_element

    return line_elements

def attribute_author_graphs(request, slug):
    # Attribute query parameter
    attribute = request.GET.get('attr')

    # Default attribute(total commits) if no query string is specified
    if not attribute:
        attribute = Statistic.ATTRIBUTES[0][0]

    # Get the repo object for the selected repository
    repo = Repository.objects.get(name = slug)

    # Get start and end date of date range
    start, end = util.get_date_range(request)

    # Get every author with displayed repo; limit 5
    # TODO: Limit by top contributors
    authors = Author.objects.filter(repos__in=[repo])[:5]

    # Generate a graph for each author based on selected attribute for the displayed repo
    line_elements = ""
    for author in authors:
        line_element = generate_graph_data(repo=repo, start=start, end=end, author=author, attribute=attribute)
        line_elements += line_element

    return line_elements

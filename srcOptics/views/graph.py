from django.shortcuts import render
from django.template import loader
from django.db.models import Sum
from django.http import *
from django_tables2 import RequestConfig
from datetime import datetime, timedelta



from ..models import Repository, Commit, Statistic, Tag
from .tables import *

from random import randint

import plotly.graph_objs as go
import plotly.offline as opy

graph_color = 'rgba(100, 50, 125, 1.0)'

"""
View basic graph for a repo
"""

#Creates bar graph and returns bar graph element
def create_bar_graph(title, x_axis_title, y_axis_title, x_axis_data, y_axis_data):
    # use plotly to make the graph
    # its html will be added to the data field of the context
    trace = go.Bar(
        x=x_axis_data,
        y=y_axis_data,
        marker=dict(color=graph_color,line=dict(color=graph_color,width=1)),
        name='Commits',
        orientation='v',
    )
    layout = go.Layout(
        title=title,
        margin={
            # 'l':50,
            # 'r':50,
            # 'b':100,
            # 't':100,
            # 'pad':20
        },
        xaxis={
            'title':x_axis_title,
            'tickfont':{
                'color': '#696969',
                'size': 18,
            }
        },
        yaxis={
            'title':y_axis_title,
            'tickfont':{
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


#Creates and returns the HTML for a scatter plot.
def create_scatter_plot(title, x_axis_title, y_axis_title, x_axis_data, y_axis_data):
    # Create traces
    trace0 = go.Scatter(
        x = x_axis_data,
        y = y_axis_data,
        mode = 'lines+markers',
        name = 'lines+markers',
        marker= dict(size= 14,
                    line= dict(width=1),
                    color= graph_color,
                   ),
        ) # The hover text goes here...

    layout = go.Layout(
        title=title,
        xaxis={
            'title':x_axis_title,
        },
        yaxis={
            'title':y_axis_title,
        },
    )
    fig = go.Figure(data = [trace0], layout=layout)
    element = opy.plot(fig, auto_open=False, output_type='div')
    return element

def attributes_by_repo(request):

    #list of possible attribute values to filter by. Defined in models.py for Statistic object
    attributes = Statistic.ATTRIBUTES
    #start date query parameter
    start = request.GET.get('start')
    #end date query parameterd
    end = request.GET.get('end')
    #attribute query parameter
    attribute = request.GET.get('attr')
    #search filter query parameter
    search = request.GET.get('filter')

    #If there isn't a filter query parameter, list all repository organization
    #TODO: filter by organization
    if not search:
        repos = Repository.objects.all()
    else:
        #If there is a filter query parameter, list repositories which match the filter
        #This includes repository name and repository tags
        #Note that a filter "ta" will return repos with the tag "tag1"
        repos = Repository.objects.filter(name__icontains=search)
        tag_query = Tag.objects.filter(name__icontains=search)
        for tag in tag_query:
            #Join the repos meeting the filter to the queryset
            repos |= tag.repos.all()



    #If start or end query parameters aren't defined, default to the last week starting from current day
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
    else:
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')

    # Default attribute(total commits)if no query string is specified
    if not attribute:
        attribute = Statistic.ATTRIBUTES[0][0]
    line_elements = ""
    #Iterate over repo queryset
    for r in repos:
        #array for dates
        dates = []
        #array for attribute values
        attribute_by_date = []
        #Filter Rollup table for daily interval statistics for the current repository over the specified time range
        stats_set = Statistic.objects.filter(interval='DY', repo=r, author=None, start_date__range=(start, end))
        #aggregate_data = stats_set.aggregate(data=Sum(attribute))


        #adds dates and attribute values to their appropriate arrays to render into graph data
        for stat in stats_set:
            dates.append(stat.start_date)
            attribute_by_date.append(getattr(stat, attribute))

        #creates a scatter plot for each repository
        line_element = create_scatter_plot(r.name, "Date", attribute.replace("_", " ").title(), dates, attribute_by_date)
        line_elements = line_elements + line_element



    context = {
        'title': "Repo Statistics Over Time",
        'data' : line_elements,
        'attribute': attributes
    }
    return render(request, 'repo_view.html', context=context)


def attribute_graphs(request, slug):

    #list of possible attribute values to filter by. Defined in models.py for Statistic object
    attributes = Statistic.ATTRIBUTES
    #start date query parameter
    start = request.GET.get('start')
    #end date query parameterd
    end = request.GET.get('end')

    #If there isn't a filter query parameter, list all repository organization
    #TODO: filter by organization
    repo = Repository.objects.get(name = slug )

    #If start or end query parameters aren't defined, default to the last week starting from current day
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
    else:
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')

    line_elements = ""
    for attribute in attributes:
        #array for dates
        dates = []
        #array for attribute values
        attribute_by_date = []
        #Filter Rollup table for daily interval statistics for the current repository over the specified time range
        stats_set = Statistic.objects.filter(interval='DY', repo=repo, author=None, start_date__range=(start, end))
        #aggregate_data = stats_set.aggregate(data=Sum(attribute))


        #adds dates and attribute values to their appropriate arrays to render into graph data
        for stat in stats_set:
            dates.append(stat.start_date)
            attribute_by_date.append(getattr(stat, attribute[0]))

        #creates a scatter plot for each element
        line_element = create_scatter_plot(repo.name, "Date", attribute[0].replace("_", " ").title(), dates, attribute_by_date)
        line_elements = line_elements + line_element


    return line_elements, attributes

# contributor note: the django UI will be eventually replaced by a new dynamic frontend speaking to the REST API, do not add features

from django.db.models import Sum, Count

from ...models import Repository, Commit, Statistic, Tag, Author

from plotly import tools
from .. import util

from .. import graph

import plotly.graph_objs as go
import plotly.offline as opy
import math

class AuthorGraph:
    def __init__(self, **kwargs):
        self.interval = kwargs['q']['interval']
        self.repo = kwargs['repo']
        self.start = kwargs['q']['start']
        self.end = kwargs['q']['end']
        self.attribute = kwargs['q']['attribute']
        self.page = int(kwargs['q']['page'])
        self.range = 6


    def top_graphs(self):

        # Get the top contributors to be graphed
        authors = util.get_top_authors(repo=self.repo, start=self.start, end=self.end, attribute=self.attribute)

        p_start = (self.page-1) * self.range
        if len(authors) < self.range * self.page:
            diff = len(authors) - p_start
            p_end = p_start + diff
        else:
            p_end = p_start + self.range

        figure = []
        # Generate a graph for each author based on selected attribute for the displayed repo
        figure = tools.make_subplots(
            rows=math.ceil(self.range/2),
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.1,
            subplot_titles=tuple([_.email for _ in authors[p_start:p_end]])
        )
        figure['layout'].update(height=800)
        for i in range(p_start, p_end):
            figure = graph.generate_graph_data(
                figure=figure,
                repo=self.repo,
                interval=self.interval,
                name=authors[i].email,
                start=self.start,
                end=self.end,
                author=authors[i],
                attribute=self.attribute,
                row=math.floor((i-p_start)/2) + 1,
                col=(( (i-p_start) % 2 )+1)

            )

        if figure:
            graph_obj = opy.plot(figure, auto_open=False, output_type='div')

            return graph_obj

        return None

class AuthorContributeGraph:
    def __init__(self, **kwargs):
        self.interval = kwargs.get('interval') if kwargs.get('interval') else 'DY'
        self.author = kwargs['author']
        self.start = kwargs['start']
        self.end = kwargs['end']
        self.attribute = kwargs['attribute']

    # show author contributions per repo
    def top_graphs(self):

        repos = self.author.repos.all()
        figure = []
        # Generate a graph for each author based on selected attribute for the displayed repo
        if repos.count() != 0:
            figure = tools.make_subplots(
                rows=math.ceil(len(repos)/2),
                cols=2,
                shared_xaxes=True,
                vertical_spacing=0.1,
                shared_yaxes=False,
                subplot_titles=tuple([_.name for _ in repos]),
            )
            figure['layout'].update(height=800)

        # list 4 repos
        for i in range(min(len(repos), 6)):
            figure = graph.generate_graph_data(
                figure=figure,
                repo=repos[i],
                interval=self.interval,
                name=repos[i].name,
                start=self.start,
                end=self.end,
                author=self.author,
                attribute=self.attribute,
                row=math.floor(i/2) + 1,
                col=( i % 2 )+1

            )

        if figure != []:
            graph_obj = opy.plot(figure, auto_open=False, output_type='div')

            return graph_obj

        return None

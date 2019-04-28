from django.db.models import Sum, Count

from ...models import Repository, Commit, Statistic, Tag, Author

from plotly import tools

from .. import graph

import plotly.graph_objs as go
import plotly.offline as opy
import math

class RepositoryGraph:
    def __init__(self, **kwargs):
        self.repos = kwargs['repos']
        self.start = kwargs['q']['start']
        self.end = kwargs['q']['end']
        self.attribute = kwargs['q']['attribute']
        self.interval = kwargs['q']['interval']
        self.page = int(kwargs['q']['page'])
        self.range = 3



    def attributes_by_repo(self):

        p_start = (self.page-1) * self.range
        if len(self.repos) < self.range * self.page:
            p_start = (self.page-1) * self.range
            p_end = p_start + (self.range * self.page) - len(self.repos) - 1
        else:
            p_start = (self.page-1) * self.range
            p_end = p_start + self.range

        if len(self.repos) == 0:
            return None

        print(self.repos)

        figure = tools.make_subplots(
            rows=self.range,
            cols=1,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.1,
            subplot_titles=tuple([_.name for _ in self.repos[p_start:p_end]]),
        )


        # Iterate over repo queryset, generating attribute graph for each
        print(p_start, p_end)
        for i in range(p_start, p_end):
            figure = graph.generate_graph_data(
                figure=figure,
                repo=self.repos[i],
                name=self.repos[i].name,
                start=self.start,
                end=self.end,
                attribute=self.attribute,
                interval=self.interval,
                row=i-p_start+1,
                col=1
            )
        figure['layout'].update(height=1000)

        data = opy.plot(figure, auto_open=False, output_type='div')

        return data

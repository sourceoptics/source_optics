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
        self.start = kwargs['start']
        self.end = kwargs['end']
        self.attribute = kwargs['attribute']
        self.interval = kwargs['interval']

    def attributes_by_repo(self):
        figure = tools.make_subplots(
            rows=len(self.repos),
            cols=1,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.1,
            subplot_titles=tuple([_.name for _ in self.repos]),
        )
        # Iterate over repo queryset, generating attribute graph for each
        for i in range(len(self.repos)):
            figure = graph.generate_graph_data(
                figure=figure,
                repo=self.repos[i],
                name=self.repos[i].name,
                start=self.start,
                end=self.end,
                attribute=self.attribute,
                interval=self.interval,
                row=i+1,
                col=1
            )
        figure['layout'].update(height=800)

        data = opy.plot(figure, auto_open=False, output_type='div')

        return data

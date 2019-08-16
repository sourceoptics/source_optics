import plotly.express as px
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from ...models import Repository
from ... plugins.report_api.flex_graph import Plugin as FlexGraph

from plotly.subplots import make_subplots
import plotly.graph_objects as go

class Command(BaseCommand):
    help = 'draws 3d graphs'

    # EX: python manage.py longtail_map -r <repo_name> -a earliest_commit,latest_commit,commits -p author
    # EX: python manage.py longtail_map -r <repo_name> -a month,authors,commits -p month

    def add_arguments(self, parser):

        parser.add_argument('-r', '--repo', dest='repo', type=str, help='report stats on this repo name', default=None)
        parser.add_argument('-a', '--aspects', dest='aspects', type=str, help='graph these aspects', default=None)
        parser.add_argument('-p', '--partition', dest='partition', type=str, help='partition by this aspect', default=None)


    def handle(self, *args, **kwargs):

        # 2D for now, because work in progress...

        repo = kwargs['repo']
        aspects = kwargs['aspects'].split(',')
        partition = kwargs['partition']

        assert repo is not None

        repos = Repository.objects.filter(name=repo)
        repo = repos.first()

        report = FlexGraph().generate(repos=repos, arguments=dict(aspects=aspects, partition=partition))
        data = report['reports'][repo.name]

        for row in data:
            print(row)

        fig = go.Figure(
            data = go.Scatter3d(
                x=[a[1] for a in data],
                z=[a[2] for a in data],
                y=[a[3] for a in data],
                opacity=0.5
            )
        )

        fig.update_layout(scene=dict(
                xaxis_title=aspects[0],
                yaxis_title=aspects[1],
                zaxis_title = aspects[2],

        )
        )

        fig.show()


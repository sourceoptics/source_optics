import plotly.express as px
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from ...models import Repository
from ... plugins.report_api.bucket_graph import Plugin as BucketGraph

from plotly.subplots import make_subplots
import plotly.graph_objects as go

class Command(BaseCommand):
    help = 'dumps raw aggregated statistics from the database, mostly for debug purposes'

    # EX: python manage.py longtail_map -r <repo_name> -e 50 -b 500 -c commits

    def add_arguments(self, parser):

        parser.add_argument('-r', '--repo', dest='repo', type=str, help='report stats on this repo name', default=None)
        parser.add_argument('-e', '--each_bucket', dest='each_bucket', type=str, help='width of bucket', default=None)
        parser.add_argument('-b', '--bucket_max', dest='bucket_max', type=str, help='max bucket size', default=None)
        # FIXME: only commits is implemented for now.
        parser.add_argument('-m', '--metric', dest='metric', type=str, help='what stat to bucketize)', default='commits')


    def handle(self, *args, **kwargs):

        # 2D for now, because work in progress...

        repo = kwargs['repo']
        each_bucket = kwargs.get('each_bucket', 50)
        bucket_max = kwargs.get('bucket_max', 500)
        metric = kwargs.get('metric', 'commits')

        assert repo is not None

        repos = Repository.objects.filter(name=repo)
        repo = repos.first()

        report = BucketGraph().generate(repos=repos, arguments=dict(each_bucket=each_bucket, bucket_max=bucket_max, metric='commits'))
        data = report['reports'][repo.name]

        for row in data:
            print(row)

        fig = go.Figure(
            data = go.Mesh3d(
                x=[a[0] for a in data],
                z=[a[1] for a in data],
                y=[a[2] for a in data],
                opacity=0.5
            )
        )

        fig.update_layout(scene=dict(
                xaxis_title='month',
                zaxis_title='author count',
                yaxis_title='LoC changed'
            )
        )

        fig.show()

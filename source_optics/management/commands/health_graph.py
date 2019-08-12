import plotly.express as px
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from ...models import Repository
from ... plugins.report_api.comm_health import Plugin as CommHealth

from plotly.subplots import make_subplots
import plotly.graph_objects as go

class Command(BaseCommand):
    help = 'dumps raw aggregated statistics from the database, mostly for debug purposes'

# EX: python manage.py health_graph -o <repo_name>

    def add_arguments(self, parser):
        parser.add_argument('-r', '--repo', dest='repo', type=str, help='report stats on this repo name', default=None)

    def _trace(self, fig, data, row, col, mode='markers'):
        print("generating...")
        fig.add_trace(
            go.Scatter(
                mode=mode,
                x=[a[0] for a in data],
                y=[a[1] for a in data],
            ),
            row=row,
            col=col
        )

    def handle(self, *args, **kwargs):

        repo = kwargs['repo']
        assert repo is not None

        repos = Repository.objects.filter(name=repo)
        repo = repos.first()


        commHealth = CommHealth()
        data = commHealth.generate(repos=repos)

        data = data['reports'][repo.name]

        # print(data)


        fig = make_subplots(rows=4, cols=2, subplot_titles=[
            'Earliest vs Latest Commit',
            'Earliest vs Commit Count',
            'Earliest vs Lines Changed',
            'Latest vs Commmit Count',
            'Latest vs Lines Changed',
            'Contributors Per Month',
            'Commits Per Month',
            'Lines Changed Per Month',
        ])

        data1 = data['earliest_vs_latest']

        self._trace(fig, data['earliest_vs_latest'], 1, 1)
        self._trace(fig, data['earliest_vs_commits'], 1, 2)
        self._trace(fig, data['earliest_vs_changed'], 2, 1)
        self._trace(fig, data['latest_vs_commits'], 2, 2)
        self._trace(fig, data['latest_vs_changed'], 3, 1)
        self._trace(fig, data['commits_per_month'], 3, 2, mode='markers+lines')
        self._trace(fig, data['contributors_per_month'], 4, 1, mode='markers+lines')
        self._trace(fig, data['changed_per_month'], 4, 2, mode='markers+lines')


        #fig.update_layout(height=600, width=800, title_text="Subplots")
        fig.show()

        #repo_report['earliest_vs_latest'] = self._earliest_vs_latest(repo=repo, authors=authors)
        #repo_report['earliest_vs_commits'] = self._earliest_vs_commits(repo=repo, authors=authors)
        #repo_report['earliest_vs_changed'] = self._earliest_vs_changed(repo=repo, authors=authors)
        #repo_report['latest_vs_commits'] = self._latest_vs_commits(repo=repo, authors=authors)
        #repo_report['latest_vs_changed'] = self._latest_vs_changed(repo=repo, authors=authors)
        #repo_report['contributors_per_month'] = self._contributors_per_month(repo=repo)
        #repo_report['commits_per_month'] = self._commits_per_month(repo=repo)
        #repo_report['changed_per_month'] = self._changed_per_month(repo=repo)

        #print(data)

        #dataframe = pd.DataFrame(data, columns = ['Earliest', 'Latest'])

        #iris = px.data.iris()
        #fig = px.scatter(dataframe, x="Earliest", y="Latest")
        #fig.show()


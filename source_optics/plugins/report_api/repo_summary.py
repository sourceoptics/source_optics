
# Copyright 2018 SourceOptics Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# About this plugin
# =================
# this plugin generates information suitable for a front-page report about repo statistics
# over a selected interval - lines added, removed, commit counts, number of authors
# participating. Returns overall stats and stats for each contributor.
# Use other plugins for graph data or deeper analysis.

from django.db.models import Sum, Max
from ... models import Statistic, Commit


class Plugin(object):

    def _get_aggregation(self, repo=None, start=None, end=None, days=0, interval='DY', author=None):

        assert repo is not None
        assert start is not None
        assert end is not None
        assert interval in ['DY','WK','MN']

        totals = None

        if author is None:

            totals = Statistic.objects.filter(
                interval='DY',  # control not needed here
                repo=repo,
                author__isnull=True,
                start_date__range=(start, end)
            )
        else:
            totals = Statistic.objects.filter(
                interval='DY',  # control not needed here
                repo=repo,
                author=author,
                start_date__range=(start, end)

            )

        for t in totals.all():
            print("AUTHOR TOTAL=", t.author_total)

        # print("DEBUG: totals=", totals)

        totals = totals.aggregate(
            lines_added=Sum('lines_added'),
            lines_removed=Sum('lines_removed'),
            commits=Sum('commit_total'),
            authors=Max('author_total')
        )

        # print("----")

        return dict(
            lines_added=totals['lines_added'],
            lines_removed=totals['lines_removed'],
            commits=totals['commits'],
            authors=totals['authors']
        )

    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None):

        data = dict()

        # add information about this plugin

        data['meta'] = dict(
            title = 'Repo Summary',
            format = 'report'
        )

        data['repos'] = dict()

        for repo in repos.all():

            # add overall info ...

            item = data['repos'][repo.name] = dict()
            item['overall'] = self._get_aggregation(repo=repo, start=start, end=end, days=days, interval=interval, author=None)

            # add per-author info...

            by_author = item['by_author'] = dict()
            author_ids = Commit.objects.filter(repo=repo).values_list('author__pk', flat=True).distinct().all()
            repo_authors = authors.filter(pk__in=author_ids)

            for author in repo_authors.all():
                author_result = self._get_aggregation(repo=repo, start=start, end=end, days=days, interval=interval, author=author)
                item = by_author[author.email] = author_result


        return data

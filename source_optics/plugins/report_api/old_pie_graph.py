# OBSOLETE - this will be folded back into the main UI

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
#

from django.db.models import Sum, Max
from ... models import Statistic, Commit, Author

# use flex_graph instead!

# FIXME: throughout the code, we have 'commit_total' and not 'commits' ... commits would seemingly make more sense
# because the other elements are totals. Consider a global replacement.

ASPECTS = [ 'lines_added', 'lines_removed', 'commit_total' ]

# About this plugin
# =================
# this plugin generates information suitable for a pie-graph report about the total contribution of
# each user compared to a total for a variety of aspects.  The information is not different from
# that which is returned by repo_summary but is structured differently.

class Plugin(object):

    def _get_pie(self, repo=None, start=None, end=None, days=0, interval='DY', author=None):

        pie = dict()



        assert repo is not None
        assert start is not None
        assert end is not None
        assert interval in ['DY', 'WK', 'MN']

        # FIXME: this gets all authors, not just those in the time range, we may wish to change this

        author_ids = Commit.objects.filter(repo=repo).values_list('author__pk', flat=True).distinct().all()
        repo_authors = Author.objects.filter(pk__in=author_ids)

        totals = Statistic.objects.filter(
            interval=interval,  # control not needed here
            repo=repo,
            author__isnull=True,
            start_date__range=(start, end)
        )

        for aspect in ASPECTS:

            item = pie[aspect] = dict()

            totals_dict = totals.aggregate(
                total=Sum(aspect)
            )
            item['total'] = totals_dict['total']
            by_author = item['by_author'] = dict()

            for author in repo_authors:
                by_author[author.email] = dict()

                author_totals = Statistic.objects.filter(
                    interval=interval,  # control not needed here
                    repo=repo,
                    author=author,
                    start_date__range=(start, end)
                )
                author_totals = author_totals.aggregate(
                    total=Sum(aspect)
                )
                by_author[author.email] = author_totals['total']

        return pie

    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None):

        data = dict()

        # add information about this plugin

        data['meta'] = dict(
            format = 'pie_graph'
        )

        data['repos'] = dict()

        for repo in repos.all():

            # add overall info ...

            item = data['repos'][repo.name] = dict()

            item['overall'] = self._get_pie(repo=repo, start=start, end=end, days=days, interval=interval, author=None)


        return data



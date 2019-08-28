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

# FIXME: DEPRECATED - use the flex_graph plugin, it is much more powerful and will be used going forward.
# by deprecated, we don't think anyone is using this, and it will be deleted whenever I feel like it.
# so, yeah...

from django.db.models import Sum, Max
from ... models import Statistic, Commit, Author

# FIXME: throughout the code, we have 'commit_total' and not 'commits' ... commits would seemingly make more sense
# because the other elements are totals. Consider a global replacement.

ASPECTS = [ 'lines_added', 'lines_removed', 'commit_total' ]

# About this plugin
# =================
# this plugin generates information for a line graph showing repo total and by-author stats over time

class Plugin(object):

    def _get_graph(self, repo=None, start=None, end=None, days=0, interval='DY', author=None, aspect=None):


        assert repo is not None
        assert start is not None
        assert end is not None
        assert interval in ['DY', 'WK', 'MN']
        assert aspect is not None

        series = dict()

        # FIXME: this gets all authors, not just those in the time range, we may wish to change this

        totals = None
        if author is None:

            totals = Statistic.objects.filter(
                interval=interval,  # control not needed here
                repo=repo,
                author__isnull=True,
                start_date__range=(start, end)
            )
        else:
            totals = Statistic.objects.filter(
                interval=interval,  # control not needed here
                repo=repo,
                author=author,
                start_date__range=(start, end)
            )

        dates = []
        data_points = []

        for stat in totals:
            dates.append(stat.start_date)
            data_points.append(getattr(stat,aspect))

        return dict(
            x=dates,
            y=data_points
        )


    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None):

        # author filter is ignored, guess that is ok for now

        if repos.count() != 1:
            raise Exception("this plugin works on only one repo at a time, try using repo_id as a parameter")

        repo = repos.first()

        data = dict()


        data['meta'] = dict(
            format = 'line_graph'
        )
        data['aspects'] = dict()

        author_ids = Commit.objects.filter(repo=repo).values_list('author__pk', flat=True).distinct().all()
        repo_authors = Author.objects.filter(pk__in=author_ids)

        for aspect in ASPECTS:

            aspect_data = data['aspects'][aspect] = dict()
            aspect_data['authors'] = dict()

            for author in repo_authors:

                author_data = aspect_data['authors'][author.email] = self._get_graph(repo=repo, start=start, end=end, days=days, interval=interval, author=author, aspect=aspect)

            total_data = aspect_data['total'] = self._get_graph(repo=repo, start=start, end=end, days=days, interval=interval, author=None, aspect=aspect)

        return data


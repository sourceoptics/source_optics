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

from django.db.models import Sum, Max
from ... models import Statistic, Commit, Author
from datetime import datetime

import json

# About this plugin
# =================
# flex graph takes the following in JSON parameters:
#  - 'show_aspect' - a list of terms
#  - 'by_aspect' - a way to partition the stats, either by 'month' or 'author'
# -
#
# it is suitable for producing 2D, 3D, and even 4D/5D graphs, because it basically returns
# list of tuples for a given repo.

# note: this plugin isn't as database efficient as many of the others
# If this becomes important we could make the scanner compile these in a table and load the new table here.


class Plugin(object):

    def ATTRIBUTE_earliest_commit(self, repo, base_queryset):
        return base_queryset.earliest("commit_date").commit_date

    def ATTRIBUTE_latest_commit(self, repo, base_queryset):
        return base_queryset.latest("commit_date").commit_date

    def ATTRIBUTE_commits(self, repo, base_queryset):
        return base_queryset.count()

    def ATTRIBUTE_authors(self, repo, base_queryset):
        authors_per_month = base_queryset.values_list('author', flat=True).distinct()
        result = len(authors_per_month)
        return result

    def ATTRIBUTE_lines_changed(self, repo, base_queryset):

        # FIXME: this statistic does NOT work when used with 'partition_month' because it needs to pass in the filtered
        # range.

        authors = base_queryset.values_list('author').distinct()

        stat = Statistic.objects.filter(
            author__in=authors,
            repo=repo,
            interval='MN'
        ).aggregate(
            lines_changed=Sum("lines_changed"),
        )
        return stat['lines_changed']

    def ATTRIBUTE_month(self, repo, base_queryset):
        a_commit = base_queryset.first()
        return datetime(month=a_commit.commit_date.month, year=a_commit.commit_date.year, day=1)

    def PARTITION_month(self, repo):

        commit_months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC').all()

        results = []
        for month in commit_months:
            print("FILT: %s, %s" % (month.year, month.month))
            results.append([ month, Commit.objects.filter(repo=repo, commit_date__year=month.year, commit_date__month=month.month) ])
        return results

    def PARTITION_author(self, repo):

        results = []
        authors = Commit.objects.filter(repo=repo).values_list('author', flat=True).distinct()
        authors = Author.objects.filter(pk__in=authors)
        for author in authors.all():
            results.append([ author.email, Commit.objects.filter(repo=repo, author=author) ])
        return results

    def _get_partitions(self, repo, partition_mode):
        # FIXME: add error handling for missing aspects
        fn = getattr(self, "PARTITION_%s" % partition_mode)
        return fn(repo)


    def _add_aspects(self, repo, partition_mode, aspects):

        rows = []

        count = 0
        for each_partition in self._get_partitions(repo, partition_mode):

            (reference, base_queryset) = each_partition

            row = [ reference ]
            count = count + 1
            print(count)

            for aspect in aspects:
                fn = getattr(self, "ATTRIBUTE_%s" % aspect)
                res = fn(repo, base_queryset)
                row.append(res)

            rows.append(row)

        return rows



    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None, arguments=None):

        # author filter is ignored, guess that is ok for now

        aspects = arguments['aspects']
        partition = arguments['partition']

        data = dict()
        data['meta'] = dict(
            format = 'data_points_by_repo'
        )
        reports = data['reports'] = dict()


        for repo in repos:

            author_ids = Commit.objects.filter(repo=repo).values_list('author__pk', flat=True).distinct().all()
            authors = Author.objects.filter(pk__in=author_ids)
            reports[repo.name] = self._add_aspects(repo, partition, aspects)

        return data

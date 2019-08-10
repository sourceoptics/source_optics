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

# FIXME: all the report API plugins have a degree of structural duplication, would be nice to reduce it.

from django.db.models import Sum, Max
from ... models import Statistic, Commit, Author


# About this plugin
# =================
# frequency vs recency gives the following stats for repos:
#
# for each contributor, intended for a scatter plot:
# - earliest commit date vs latest commit date
# - earliest commit date vs commit count
# - earliest commit date vs lines changed (added+removed)
# - latest commit date vs commit count
# - latest commit date vs lines changed (added+removed)
# - each month vs number of contributors per month

# note: this plugin isn't as database efficient as many of the others (lots of lookups!).
# If this becomes important we could make the scanner compile these in a table and load the new table here.
# Until then, this is primarily intended for occasional analysis/blog posts and may be ok as is.

class Plugin(object):

    def _earliest_commit(self, repo, author):
        return Commit.objects.filter(author=author, repo=repo).earliest("commit_date").commit_date

    def _latest_commit(self, repo, author):
        return Commit.objects.filter(author=author, repo=repo).latest("commit_date").commit_date

    def _commits(self, repo, author):
        return Commit.objects.filter(repo=repo, author=author).count()

    def _lines_changed(self, repo, author):
        stat = Statistic.objects.filter(
            repo=repo,
            author=author,
            interval='MN'
        ).aggregate(
            lines_changed=Sum("lines_changed"),
        )
        return stat['lines_changed']


    def _earliest_vs_latest(self, repo, authors):
        return [[self._earliest_commit(repo, x), self._latest_commit(repo,x)] for x in authors.all() ]

    def _earliest_vs_commits(self, repo, authors):
       return [ [self._earliest_commit(repo, x), self._commits(repo, x)] for x in authors.all() ]

    def _earliest_vs_changed(self, repo, authors):
        return [[self._earliest_commit(repo, x), self._lines_changed(repo, x)] for x in authors.all()]

    def _latest_vs_changed(self, repo, authors):
        return [[self._latest_commit(repo, x), self._lines_changed(repo, x)] for x in authors.all()]

    def _latest_vs_commits(self, repo, authors):
       return [ [self._latest_commit(repo, x), self._commits(repo, x)] for x in authors.all() ]

    def _contributors_per_month(self, repo):
        commit_months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC')
        data = []
        for start_day in commit_months:
            # this is long, sorry
            data.append([start_day, Commit.objects.filter(repo=repo, commit_date__month=start_day.month, commit_date__year=start_day.year).values_list('author').distinct().count() ])
        return data


    def _commits_per_month(self, repo):
        commit_months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC')
        data = []
        for start_day in commit_months:
            data.append([start_day, Commit.objects.filter(repo=repo, commit_date__month=start_day.month, commit_date__year=start_day.year).count() ])
        return data

    def _changed_per_month(self, repo):
        commit_months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC')
        data = []
        for start_day in commit_months:
            stat = Statistic.objects.filter(repo=repo, author__isnull=True, start_date__month=start_day.month, start_date__year=start_day.year).first()
            data.append([start_day, stat.lines_changed])
        return data

    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None):

        # author filter is ignored, guess that is ok for now


        data = dict()
        data['meta'] = dict(
            format = 'custom'
        )
        reports = data['reports'] = dict()


        for repo in repos:

            author_ids = Commit.objects.filter(repo=repo).values_list('author__pk', flat=True).distinct().all()
            authors = Author.objects.filter(pk__in=author_ids)

            repo_report = reports[repo.name] = dict()

            repo_report['earliest_vs_latest'] = self._earliest_vs_latest(repo=repo, authors=authors)
            repo_report['earliest_vs_commits'] = self._earliest_vs_commits(repo=repo, authors=authors)
            repo_report['earliest_vs_changed'] = self._earliest_vs_changed(repo=repo, authors=authors)
            repo_report['latest_vs_commits'] = self._latest_vs_commits(repo=repo, authors=authors)
            repo_report['latest_vs_changed'] = self._latest_vs_changed(repo=repo, authors=authors)
            repo_report['contributors_per_month'] = self._contributors_per_month(repo=repo)
            repo_report['commits_per_month'] = self._commits_per_month(repo=repo)
            repo_report['changed_per_month'] = self._changed_per_month(repo=repo)


        return data

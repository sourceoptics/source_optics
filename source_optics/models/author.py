# Copyright 2018-2019 SourceOptics Project Contributors
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

import functools
from django.db import models
from django.db.models import Sum

class Author(models.Model):

    email = models.CharField(db_index=True, max_length=512, unique=True, blank=False, null=True)
    display_name = models.CharField(db_index=True, max_length=512, unique=False, blank=True, null=True)
    alias_for = models.ForeignKey('self', blank=True, null=True, related_name='alias_of', on_delete=models.SET_NULL)

    def get_display_name(self):
        if self.display_name:
            return self.display_name
        return self.email

    def __str__(self):
        return f"Author: {self.display_name} <{self.email}>"

    @functools.lru_cache(maxsize=128, typed=False)
    def earliest_commit_date(self, repo):
        return Commit.objects.filter(author=self, repo=repo).earliest("commit_date").commit_date

    @functools.lru_cache(maxsize=128, typed=False)
    def latest_commit_date(self, repo):
        return Commit.objects.filter(author=self, repo=repo).latest("commit_date").commit_date

    @classmethod
    def cache_clear(cls):
        cls.earliest_commit_date.cache_clear()
        cls.latest_commit_date.cache_clear()
        cls.authors.cache_clear()
        cls.author_count.cache_clear()

    def statistics(self, repo, start=None, end=None, interval=None):
        from . statistic import Statistic
        # FIXME: we should be using annotate in most places, move away from this?
        assert start is not None
        assert end is not None
        assert interval is not None
        stat = Statistic.objects.filter(
            repo=repo,
            author=self,
            interval=interval,
            start_date__range=(start, end)
        ).aggregate(
            lines_added=Sum('lines_added'),
            lines_changed=Sum('lines_removed'),
            lines_removed=Sum('lines_removed'),
            commit_total=Sum('commit_total'),
            moves=Sum('moves'),
            edits=Sum('edits'),
            creates=Sum('creates')
        )
        return stat

    @functools.lru_cache(maxsize=128, typed=False)
    def repos(self, start=None, end=None):
        from . commit import Commit
        if start is not None:
            qs = Commit.objects.filter(
                author=self,
                commit_date__range=(start, end)
            )
        else:
            qs = Commit.objects.filter(
                author=self
            )
        repo_ids = qs.values_list('repo', flat=True).distinct('repo')
        return Repository.objects.filter(pk__in=repo_ids)

    @classmethod
    @functools.lru_cache(maxsize=128, typed=False)
    def authors(cls, repo, start=None, end=None):
        from . commit import Commit
        assert repo is not None
        qs = None
        if start is not None:
            if isinstance(repo, str):
                qs = Commit.objects.filter(
                    author__isnull=False,
                    repo__name=repo,
                    commit_date__range=(start, end)
                )
            else:
                qs = Commit.objects.filter(
                    author__isnull=False,
                    repo=repo,
                    commit_date__range=(start, end)
                )
        else:
            qs = Commit.objects.filter(
                repo=repo,
                author__isnull=False,
            )
        author_ids = qs.values_list('author', flat=True).distinct('author')
        return Author.objects.filter(pk__in=author_ids)

    @classmethod
    @functools.lru_cache(maxsize=128, typed=False)
    def author_count(cls, repo, start=None, end=None):
        return cls.authors(repo, start=start, end=end).count()

    @functools.lru_cache(maxsize=128, typed=False)
    def files_changed(self, repo):
        from . file import File
        return File.objects.select_related('file_changes', 'commit').filter(
            repo=repo,
            file_changes__commit__author=self,
        ).distinct('path').count()
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
from django.db.models import Sum, Max
from . file import File

class FileChange(models.Model):

    file = models.ForeignKey('File', db_index=True, on_delete=models.CASCADE, related_name='file_changes', null=False)
    commit = models.ForeignKey('Commit', db_index=True, on_delete=models.CASCADE, related_name='file_changes')
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)
    # the following are kept as ints for quick aggregation
    is_create = models.IntegerField(default=0)
    is_move = models.IntegerField(default=0)
    is_edit = models.IntegerField(default=0)

    class Meta:
        unique_together = [ 'file', 'commit' ]
        indexes = [
            models.Index(fields=[ 'file', 'commit' ], name='file_change2')
        ]

    @classmethod
    def queryset_for_range(cls, repos=None, authors=None, start=None, end=None):
        assert repos or authors
        objs = FileChange.objects.select_related('commit','file')
        if authors:
           objs = objs.filter(commit__author__pk__in=authors)
        if repos:
            objs = objs.filter(commit__repo__pk__in=repos)
        if start:
            objs = objs.filter(commit__commit_date__range=(start,end))
        return objs

    @classmethod
    def aggregate_stats(cls, repo, author=None, start=None, end=None):
        # the placement of this method is a little misleading as it deals in files, file changes, and commits
        # it likely could be a lot more efficient by building a custom SQL query here


        authors = None
        repos = None
        if author:
            authors = [ author.pk ]
        if repo:
            repos = [ repo.pk ]

        qs = cls.queryset_for_range(repos=repos, authors=authors, start=start, end=end)
        files = File.queryset_for_range(repos=repos, authors=authors, start=start, end=end)
        stats = qs.aggregate(
            lines_added=Sum("lines_added"),
            lines_removed = Sum("lines_removed"),
            moves = Sum("is_move"),
            edits = Sum("is_edit"),
            creates = Sum("is_create"),
        )
        # FIXME: we should be able to aggregrate the count and make this less expensive
        stats['commit_total'] = qs.values_list('commit', flat=True).distinct().count()
        # FIXME: this should also have a LRU - use the file count method in File
        stats['files_changed'] = files.count()
        stats['lines_changed'] = stats['lines_added'] + stats['lines_removed']
        return stats

    @classmethod
    @functools.lru_cache(maxsize=128, typed=False)
    def change_count(cls, repo, author=None, start=None, end=None):
        if author:
            qs = cls.queryset_for_range(repos=[repo.pk], authors=[author.pk], start=start, end=end)
        else:
            qs = cls.queryset_for_range(repos=[repo.pk], start=start, end=end)
        return qs.count()

    @classmethod
    def cache_clear(cls):
        cls.change_count.cache_clear()

    def __str__(self):
        return f"FileChange: {self.file.path} {self.file.commit.sha})"
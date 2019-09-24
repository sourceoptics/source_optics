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

from django.db import models

class Commit(models.Model):

    repo = models.ForeignKey('Repository', db_index=True, on_delete=models.CASCADE, related_name='commits')
    author = models.ForeignKey('Author', db_index=True, on_delete=models.CASCADE, blank=False, null=True, related_name='commits')
    sha = models.CharField(db_index=True, max_length=512, blank=False)
    commit_date = models.DateTimeField(db_index=True,blank=False, null=True)
    author_date = models.DateTimeField(blank=False, null=True)
    subject = models.TextField(db_index=True, blank=False)

    class Meta:
        unique_together = [ 'repo', 'sha' ]
        indexes = [
            models.Index(fields=['commit_date', 'author', 'repo'], name='commit3'),
            models.Index(fields=['author_date', 'author', 'repo'], name='commit4'),
            models.Index(fields=['author', 'repo'], name='commit5'),

        ]

    @classmethod
    def queryset_for_range(cls, repos, authors, start=None, end=None):

        assert repos or authors

        objs = cls.objects

        if authors:
            objs = objs.filter(author__pk__in=authors)
        if repos:
            objs = objs.filter(repos__pk__in=repos)
        if start:
            assert end is not None
            objs = objs.filter(commit_date__range=(start,end))
        return objs

    def __str__(self):
        return f"Commit: {self.sha} (r:{self.repo.name})"

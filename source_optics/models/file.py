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

class File(models.Model):

    repo = models.ForeignKey('Repository', db_index=True, on_delete=models.CASCADE, related_name='+', null=True)
    name = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    path = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    ext = models.TextField(max_length=32, blank=False, null=True)
    binary = models.BooleanField(default=False)
    created_by = models.ForeignKey('Commit', on_delete=models.CASCADE, related_name='files', null=True)

    class Meta:
        unique_together = [ 'repo', 'name', 'path' ]
        indexes = [
            models.Index(fields=[ 'repo', 'name', 'path' ], name='file2')
        ]

    @classmethod
    def queryset_for_range(cls, repos=None, authors=None, start=None, end=None):
        assert start is not None
        assert end is not None
        assert repos or authors

        objs = File.objects.select_related('file_changes', 'commit')

        if authors:
            objs = objs.filter(file_changes__commit__author__pk__in=authors)
        if repos:
            objs = objs.filter(repo__pk__in=repos)
        return objs

    def __str__(self):
        return f"File: ({self.repo}) {self.path}/{self.name})"
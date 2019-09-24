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
import re
from django.db import models
from . commit import Commit

repo_validator = re.compile(r'[^a-zA-Z0-9._\-]')

def validate_repo_name(value):
    if re.search(repo_validator, value):
        raise ValidationError("%s is not a valid repo name" % value)

class Repository(models.Model):

    name = models.CharField(db_index=True, max_length=64, blank=False, null=False, validators=[validate_repo_name])

    organization = models.ForeignKey('Organization', db_index=True, on_delete=models.SET_NULL, null=True, related_name='repos')
    enabled = models.BooleanField(default=True, help_text='if false, disable scanning')
    last_scanned = models.DateTimeField(blank=True, null=True)

    last_pulled = models.DateTimeField(blank = True, null = True)
    url = models.CharField(max_length=255, db_index=True, blank=False, help_text='use a git ssh url for private repos, else http/s are ok')

    force_next_pull = models.BooleanField(null=False, default=False, help_text='used by webhooks to signal the scanner')
    webhook_token = models.CharField(max_length=255, null=True, blank=True, help_text='prevents against trivial webhook spam')
    force_nuclear_rescan = models.BooleanField(null=False, default=False, help_text='on next scan loop, delete all commits/records and rescan everything')

    scanner_directory_allow_list = models.TextField(null=True, blank=True,
                                                    help_text='if set, fnmatch patterns of directories to require, one per line')
    scanner_directory_deny_list = models.TextField(null=True, blank=True,
                                                   help_text='fnmatch patterns or prefixes of directories to exclude, one per line')
    scanner_extension_allow_list = models.TextField(null=True, blank=True,
                                                    help_text='if set, fnmatch patterns of extensions to require, one per line')
    scanner_extension_deny_list = models.TextField(null=True, blank=True,
                                                   help_text='fnmatch patterns or prefixes of extensions to exclude, one per line ')

    class Meta:
        unique_together = [ 'name', 'organization' ]
        indexes = [
            models.Index(fields=[ 'name', 'organization' ])
        ]
        verbose_name_plural = "repositories"

    def __str__(self):
        return self.name

    # this is only used in the scanner, so LRU cache should be ok.
    @functools.lru_cache(maxsize=128, typed=False)
    def earliest_commit_date(self, author=None):

        # FIXME: duplication with Author class below, remove the author option


        commits = Commit.objects
        if author:
            commits = commits.filter(author=author, repo=self)
        else:
            commits = commits.filter(repo=self)
        if commits.count():
            return commits.earliest("commit_date").commit_date
        return None

    # this is only used in the scanner, so LRU cache should be ok.
    @functools.lru_cache(maxsize=128, typed=False)
    def latest_commit_date(self, author=None):

        # FIXME: duplication with Author class below, remove the author option

        commits = Commit.objects
        if author:
            commits = commits.filter(author=author, repo=self)
        else:
            commits = commits.filter(repo=self)
        if commits.count():
            return commits.latest("commit_date").commit_date
        return None

    @functools.lru_cache(maxsize=128, typed=False)
    def author_ids(self, start=None, end=None):
        if start:
            return [ x[0] for x in Commit.objects.filter(repo=self, commit_date__range=(start, end)).values_list('author').distinct() ]
        else:
            return [ x[0] for x in Commit.objects.filter(repo=self).values_list('author').distinct() ]


    @classmethod
    def cache_clear(cls):
        cls.author_ids.cache_clear()
        cls.earliest_commit_date.cache_clear()
        cls.latest_commit_date.cache_clear()
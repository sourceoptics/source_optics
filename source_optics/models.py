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

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import BrinIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from source_optics.scanner.encrypt import SecretsManager

# FIXME: move each model to a seperate file (not urgent)

repo_validator = re.compile(r'[^a-zA-Z0-9._]')

def validate_repo_name(value):
    if re.search(repo_validator, value):
        raise ValidationError("%s is not a valid repo name" % value)

def cache_clear():
    Organization.cache_clear()
    Repository.cache_clear()
    FileChange.cache_clear()
    Author.cache_clear()

class Organization(models.Model):

    name = models.CharField(max_length=255, db_index=True, blank=False, unique=True)
    admins = models.ManyToManyField(User, related_name='+', help_text='currently unused')
    members = models.ManyToManyField(User, related_name='+', help_text='currently unused')
    credential = models.ForeignKey('Credential', on_delete=models.SET_NULL, null=True, help_text='used for repo imports and git checkouts')

    webhook_enabled = models.BooleanField(default=False)
    webhook_token = models.CharField(max_length=255, null=True, blank=True)

    checkout_path_override = models.CharField(max_length=512, null=True, blank=True, help_text='if set, override the default checkout location')

    scanner_directory_allow_list = models.TextField(null=True, blank=True, help_text='if set, fnmatch patterns of directories to require, one per line')
    scanner_directory_deny_list = models.TextField(null=True, blank=True, help_text='fnmatch patterns or prefixes of directories to exclude, one per line')
    scanner_extension_allow_list = models.TextField(null=True, blank=True, help_text='if set, fnmatch patterns of extensions to require, one per line')
    scanner_extension_deny_list = models.TextField(null=True, blank=True, help_text='fnmatch patterns or prefixes of extensions to exclude, one per line ')

    def __str__(self):
        return self.name

    @functools.lru_cache(maxsize=128, typed=False)
    def get_working_directory(self):
        path = settings.CHECKOUT_DIRECTORY

        if self.checkout_path_override:
            path = self.checkout_path_override

        return path

    @classmethod
    def cache_clear(cls):
        cls.get_working_directory.cache_clear()

class Credential(models.Model):

    name = models.CharField(max_length=255, blank=False, db_index=True)
    username = models.CharField(max_length=64, blank=True, help_text='for github/gitlab username')
    password = models.CharField(max_length=255,  blank=True, null=True, help_text='for github/gitlab imports')
    ssh_private_key = models.TextField(blank=True, null=True, help_text='for cloning private repos')
    ssh_unlock_passphrase = models.CharField(max_length=255, blank=True, null=True, help_text='for cloning private repos')
    description = models.TextField(max_length=1024, blank=True, null=True)
    organization_identifier = models.CharField(max_length=256, blank=True, null=True, help_text='for github/gitlab imports')
    import_filter = models.CharField(max_length=255, blank=True, null=True, help_text='if set, only import repos matching this fnmatch pattern')
    api_endpoint = models.CharField(max_length=1024, blank=True, null=True, help_text="for github/gitlab imports off private instances")

    class Meta:
        verbose_name = 'Credential'
        verbose_name_plural = 'Credentials'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        mgr = SecretsManager()
        self.password = mgr.cloak(self.password)
        self.ssh_private_key = mgr.cloak(self.ssh_private_key)
        self.ssh_unlock_passphrase = mgr.cloak(self.ssh_unlock_passphrase)
        super().save(*args, **kwargs)

    def unencrypt_password(self):
        mgr = SecretsManager()
        return mgr.uncloak(self.password)

    def unencrypt_ssh_private_key(self):
        mgr = SecretsManager()
        return mgr.uncloak(self.ssh_private_key)

    def unencrypt_ssh_unlock_passphrase(self):
        mgr = SecretsManager()
        return mgr.uncloak(self.ssh_unlock_passphrase)


class Repository(models.Model):

    name = models.CharField(db_index=True, max_length=64, blank=False, null=False, validators=[validate_repo_name])

    organization = models.ForeignKey(Organization, db_index=True, on_delete=models.SET_NULL, null=True)
    enabled = models.BooleanField(default=True, help_text='if false, disable scanning')
    last_scanned = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField('Tag', related_name='tags', blank=True)
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

class Author(models.Model):
    email = models.CharField(db_index=True, max_length=512, unique=True, blank=False, null=True)

    def __str__(self):
        return f"Author: {self.email}"

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
        )
        return stat

    @classmethod
    @functools.lru_cache(maxsize=128, typed=False)
    def authors(cls, repo, start=None, end=None):
        assert repo is not None

        # FIXME: some duplication with the method in Repo, we should retire that other method
        # FIXME: this can be written more clearly and efficiently with a related field, right?

        if start is not None:
            qs = Commit.objects.filter(
                author__isnull=False,
                repo=repo,
                commit_date__range=(start, end)
            )
        else:
            qs = Commit.objects.filter(
                author__isnull=False,
                repo=repo
            )
        author_ids = qs.values_list('author', flat=True).distinct('author')
        return Author.objects.filter(pk__in=author_ids)

    @classmethod
    @functools.lru_cache(maxsize=128, typed=False)
    def author_count(cls, repo, start=None, end=None):
        return cls.authors(repo, start=start, end=end).count()

    @functools.lru_cache(maxsize=128, typed=False)
    def files_changed(self, repo):
        return File.objects.select_related('file_changes', 'commit').filter(
            repo=repo,
            file_changes__commit__author=self,
        ).distinct('path').count()



class Tag(models.Model):
    name = models.CharField(max_length=64, db_index=True, blank=True, null=True)
    repos = models.ManyToManyField(Repository, related_name='+', blank=True)

    def __str__(self):
        return f"Tag: {self.name}"


class Commit(models.Model):

    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, related_name='commits')
    author = models.ForeignKey(Author, db_index=True, on_delete=models.CASCADE, blank=False, null=True, related_name='commits')
    sha = models.CharField(db_index=True, max_length=512, blank=False)
    commit_date = models.DateTimeField(db_index=True,blank=False, null=True)
    author_date = models.DateTimeField(blank=False, null=True)
    subject = models.TextField(db_index=True, blank=False)

    class Meta:
        unique_together = [ 'repo', 'sha' ]
        indexes = [
            BrinIndex(fields=['commit_date', 'author', 'repo'], name='commit1'),
            BrinIndex(fields=['author_date', 'author', 'repo'], name='commit2'),
        ]

    @classmethod
    def queryset_for_range(cls, repo, author=None, start=None, end=None):
        if author:
            if start:
                return cls.objects.filter(
                    repo=repo,
                    author=author,
                    commit_date__range=(start, end)
                )
            else:
                return cls.objects.filter(
                    repo=repo,
                    author=author
                )
        else:
            if start:
                return cls.objects.filter(
                    repo=repo,
                    commit_date__range=(start, end)
                )
            else:
                return cls.object.filter(repo=repo)

    def __str__(self):
        return f"Commit: {self.sha} (r:{self.repo.name})"

class File(models.Model):

    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, related_name='+', null=True)
    name = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    path = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    ext = models.TextField(max_length=32, blank=False, null=True)
    binary = models.BooleanField(default=False)

    class Meta:
        unique_together = [ 'repo', 'name', 'path' ]
        indexes = [
            BrinIndex(fields=[ 'repo', 'name', 'path' ], name='file1')
        ]

    @classmethod
    def queryset_for_range(cls, repo, author=None, start=None, end=None):
        assert start is not None
        assert end is not None
        if author:
            return File.objects.select_related('file_changes','commit').filter(
                repo=repo,
                file_changes__commit__author=author,
                file_changes__commit__commit_date__range=(start, end)
            )
        else:
            return File.objects.select_related('file_changes','commit').filter(
                repo=repo,
                file_changes__commit__commit_date__range=(start, end)
            )

    def __str__(self):
        return f"File: ({self.repo}) {self.path}/{self.name})"

class FileChange(models.Model):

    file = models.ForeignKey(File, db_index=True, on_delete=models.CASCADE, related_name='file_changes', null=False)
    commit = models.ForeignKey(Commit, db_index=True, on_delete=models.CASCADE, related_name='file_changes')
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    class Meta:
        unique_together = [ 'file', 'commit' ]
        indexes = [
            BrinIndex(fields=[ 'file', 'commit' ], name='file_change1')
        ]

    @classmethod
    def queryset_for_range(cls, repo, author=None, start=None, end=None):
        # FIXME: not the most efficient query
        if author:
            if start:
                return FileChange.objects.select_related('commit','file').filter(
                    commit__author=author,
                    commit__repo=repo,
                    commit__commit_date__range=(start, end)
                )
            else:
                return FileChange.objects.select_related('commit','file').filter(
                    commit__author=author,
                    commit__repo=repo,
                )
        else:
            if start:
                return FileChange.objects.select_related('commit','file').filter(
                    commit__repo=repo,
                    commit__commit_date__range=(start, end)
                )
            else:
                return FileChange.objects.select_related('commit', 'file').filter(commit__repo=repo)

    @classmethod
    def aggregate_stats(cls, repo, author=None, start=None, end=None):
        # the placement of this method is a little misleading as it deals in files, file changes, and commits
        # it likely could be a lot more efficient by building a custom SQL query here
        qs = cls.queryset_for_range(repo, author=author, start=start, end=end)
        files = File.queryset_for_range(repo, author=author, start=start, end=end)
        stats = qs.aggregate(lines_added=Sum("lines_added"), lines_removed = Sum("lines_removed"))
        # FIXME: there is duplication here with the Statistic class and we should figure out how to fix that.
        # FIXME: the qs call should use a LRU cache wrapped method. Isn't there a method in Commit?
        stats['commit_total'] = qs.values_list('commit', flat=True).distinct().count()
        # FIXME: this should also have a LRU - use the file count method in File
        stats['files_changed'] = files.count()
        stats['lines_changed'] = stats['lines_added'] + stats['lines_removed']
        return stats

    @classmethod
    @functools.lru_cache(maxsize=128, typed=False)
    def change_count(cls, repo, author=None, start=None, end=None):
        qs = cls.queryset_for_range(repo, author=author, start=start, end=end)
        return qs.count()

    @classmethod
    def cache_clear(cls):
        cls.change_count.cache_clear()

    def __str__(self):
        return f"FileChange: {self.file.path} {self.file.commit.sha})"


# if author = null, entry represents total stats for interval
# if author = X, entry represent X's author stats for the given interval

class Statistic(models.Model):

    INTERVALS = (
        ('DY', 'Day'),
        ('WK', 'Week'),
        ('MN', 'Month'),
        ('LF', 'Lifetime')
    )

    start_date = models.DateTimeField(blank=False, null=True)
    interval = models.TextField(max_length=5, choices=INTERVALS)
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, null=True, related_name='repo')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True, related_name='author')

    lines_added = models.IntegerField(blank = True, null = True)
    lines_removed = models.IntegerField(blank = True, null = True)
    lines_changed = models.IntegerField(blank = True, null = True)
    commit_total = models.IntegerField(blank = True, null = True)
    files_changed = models.IntegerField(blank = True, null = True)
    author_total = models.IntegerField(blank = True, null = True)
    days_active = models.IntegerField(blank=True, null=False, default=0)
    average_commit_size = models.IntegerField(blank=True, null=True, default=0)

    commits_per_day = models.FloatField(blank=True, null=True, default=0)
    files_changed_per_day = models.FloatField(blank=True, null=True, default=0)
    lines_changed_per_day = models.FloatField(blank=True, null=True, default=0)
    bias = models.IntegerField(blank=True, null=True, default=0)
    flux = models.FloatField(blank=True, null=True, default=0)
    commitment = models.FloatField(blank=True, null=True, default=0)

    # the following stats are only going to be valid for LIFETIME ('LF') intervals
    earliest_commit_date = models.DateTimeField(blank=True, null=True)
    latest_commit_date = models.DateTimeField(blank=True, null=True)
    days_since_seen = models.IntegerField(blank=False, null=True, default=-1)
    days_before_joined = models.IntegerField(blank=False, null=True, default=-1)
    longevity = models.IntegerField(blank=True, null=False, default=0)


    def __str__(self):
        if self.author is None:
            return "Stat(Total): I=" + str(self.interval[0]) + " D=" + str(self.start_date)
        else:
            return "Stat(Author): " + str(self.author) + " I=" + str(self.interval[0]) + " D=" + str(self.start_date)

    class Meta:

        unique_together = [
            [ 'start_date', 'interval', 'repo', 'author' ]
        ]

        indexes = [
            BrinIndex(fields=['start_date', 'interval', 'repo', 'author'], name='author_rollup2'),
        ]

    @classmethod
    def aggregate_data(cls, queryset):
        return queryset.aggregate(
            lines_added=Sum("lines_added"),
            lines_removed=Sum("lines_removed"),
            lines_changed=Sum("lines_changed"),
            commit_total=Sum("commit_total"),
            days_active=Sum("days_active"),
        )

    @classmethod
    def compute_interval_statistic(cls, queryset, interval=interval, repo=None, author=None, start=None, end=None, for_update=False):

        # used by rollup.py to derive a rollup interval from another.

        if interval != 'LF':
            assert start is not None
            assert end is not None
        assert repo is not None

        data = Statistic.aggregate_data(queryset)
        author_count = Author.author_count(repo, start=start, end=end)
        files_changed = FileChange.change_count(repo=repo, start=start, end=end, author=author)

        if author and isinstance(author, int):
            # FIXME: find where this is happening and make sure the system returns objects.
            author = Author.objects.get(pk=author)

        stat = Statistic(
            start_date=start,
            interval=interval,
            repo=repo,
            author=author,
            lines_added=data['lines_added'],
            lines_removed=data['lines_removed'],
            lines_changed=data['lines_changed'],
            commit_total=data['commit_total'],
            days_active=data['days_active'],
            files_changed=files_changed,
            author_total=author_count,
        )

        stat.compute_derived_values()

        if for_update and interval == 'LF':

            all_earliest = repo.earliest_commit_date()
            all_latest = repo.latest_commit_date()
            stat.earliest_commit_date = repo.earliest_commit_date(author)
            stat.latest_commit_date = repo.latest_commit_date(author)
            stat.days_since_seen = (all_latest - stat.latest_commit_date).days
            stat.days_before_joined = (stat.earliest_commit_date - all_earliest).days
            stat.longevity = (stat.latest_commit_date - stat.earliest_commit_date).days + 1
            stat.commitment = (stat.days_active / (1 + stat.longevity))

            update_stats = None
            if author:
                update_stats = Statistic.objects.filter(repo=repo, author=author)
            else:
                update_stats = Statistic.objects.filter(repo=repo, author__isnull=True)
            # these stats are somewhat denormalized 'globals' but allows us to include them efficiently in time-series tooltips which is nice.
            update_stats.update(
                earliest_commit_date = stat.earliest_commit_date,
                latest_commit_date = stat.latest_commit_date,
                days_since_seen = stat.days_since_seen,
                days_before_joined = stat.days_before_joined,
                longevity = stat.longevity,
                commitment = stat.commitment
            )

        elif not for_update and queryset.count():

            if author:
                first = queryset.first()
                stat.earliest_commit_date = first.earliest_commit_date
                stat.latest_comit_date = first.latest_commit_date
                stat.days_since_seen = first.days_since_seen
                stat.days_before_joined = first.days_before_joined
                stat.longevity = first.longevity
                stat.commitment = first.commitment
            else:
                # leave these at defaults
                pass




        return stat

    def compute_derived_values(self):
        self.average_commit_size = Statistic._div_safe(self, 'lines_changed', 'commit_total')
        self.commits_per_day = Statistic._div_safe(self, 'commit_total', 'days_active')
        self.lines_changed_per_day = Statistic._div_safe(self, 'lines_changed', 'days_active')
        self.files_changed_per_day = Statistic._div_safe(self, 'files_changed', 'days_active')
        self.flux = Statistic._div_safe(self, 'lines_changed', 'files_changed')
        if self.lines_added and self.lines_removed:
            self.bias = self.lines_added - self.lines_removed
        else:
            self.bias = 0

    @classmethod
    def _div_safe(cls, data, left, right):
        # FIXME: more of a question - these are float fields, do we want this, or should we make them int fields?
        # we're casting anyway at this point.
        if isinstance(data, dict):
            # FIXME: when done refactoring, I would think we'd only have objects, and this part
            # would no longer be needed.
            if data[right]:
                return int(float(data[left]) / float(data[right]))
            else:
                return 0
        else:
            left  = getattr(data, left, None)
            right = getattr(data, right, None)
            if left and right:
                return int(float(left) / float(right))
            else:
                return 0

    def copy_fields_for_update(self, other):
        # TODO: make this list of fields gathered automatically from the model so maintaince
        # of this function isn't required?  Get all Int + Date fields, basically
        self.lines_added = other.lines_added
        self.lines_removed = other.lines_removed
        self.lines_changed = other.lines_changed
        self.commit_total = other.commit_total
        self.files_changed = other.files_changed
        self.author_total = other.author_total
        self.earliest_commit_date = other.earliest_commit_date
        self.latest_commit_date = other.latest_commit_date
        self.days_since_seen = other.days_since_seen
        self.days_before_joined = other.days_before_joined
        self.days_active = other.days_active
        self.average_commit_size = other.average_commit_size
        self.commits_per_day = other.commits_per_day
        self.lines_changed_per_day = other.lines_changed_per_day
        self.files_changed_per_day = other.files_changed_per_day
        self.bias = other.bias
        self.flux = other.flux
        self.commitment = other.commitment
        self.longevity = other.longevity


    @classmethod
    def queryset_for_range(cls, repo, interval, author=None, start=None, end=None):
        assert repo is not None
        stats = Statistic.objects.select_related('author')
        if interval == 'LF':
            if author:
                return stats.filter(
                    author=author,
                    interval='LF',
                    repo=repo
                )
            else:
                return stats.filter(
                    author__isnull=True,
                    repo=repo,
                    interval='LF',
                )
        else:
            if author:
                return stats.filter(
                    author=author,
                    interval=interval,
                    repo=repo,
                    start_date__range=(start, end)
                )
            else:
                return stats.filter(
                    author__isnull=True,
                    interval=interval,
                    repo=repo,
                    start_date__range=(start, end)
                )


    def to_dict(self):
        # FIXME: this really should take the interval as a parameter, such that it can not
        # supply statistics that don't make sense if the interval != lifetime ('LF').
        result = dict(
            days_active=self.days_active,
            commit_total=self.commit_total,
            average_commit_size=self.average_commit_size,
            lines_changed=self.lines_changed,
            lines_added=self.lines_added,
            lines_removed=self.lines_removed,
            longevity=self.longevity,
            earliest_commit_date=str(self.earliest_commit_date),
            latest_commit_date=str(self.latest_commit_date),
            days_before_joined=self.days_before_joined,
            days_since_seen=self.days_since_seen,
            author_total=self.author_total,
            files_changed=self.files_changed,
            files_changed_per_day=self.files_changed_per_day,
            lines_changed_per_day=self.lines_changed_per_day,
            commits_per_day=self.commits_per_day,
            bias=self.bias,
            flux=self.flux,
            commitment=self.commitment
        )
        if self.author:
            result['author']=self.author.email
        else:
            result['author']=None
        return result


    def to_author_dict(self, repo, author):

        # FIXME: this is somewhat similar to the views.py aggregrate needs but slightly different,
        # as we refactor, try to consolidate the duplication. This is only used for lifetime
        # reports, that don't use the interval summing code, but can't we just sum the lifetime
        # stat as an interval of one? I think we can.  This means the extra DB lookups are redundant.

        stat2 = self.to_dict()
        # there's a LRU cache around this, but is there a better way to do this?
        stat2['files_changed'] = author.files_changed(repo)
        return stat2

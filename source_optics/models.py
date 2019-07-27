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

import re

# FIXME: remove non-database behavior from this module
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from source_optics.scanner.encrypt import SecretsManager

repo_validator = re.compile(r'[^a-zA-Z0-9._]')

def validate_repo_name(value):
    if re.search(repo_validator, value):
        raise ValidationError("%s is not a valid repo name" % value)

class Organization(models.Model):

    name = models.TextField(max_length=32, db_index=True, blank=False, unique=True)
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

    def get_working_directory(self):
        path = settings.CHECKOUT_DIRECTORY

        if self.checkout_path_override:
            path = self.checkout_path_override

        return path

class Credential(models.Model):

    name = models.TextField(max_length=64, blank=False, db_index=True)
    username = models.TextField(max_length=32, blank=True, help_text='for github/gitlab username')
    password = models.TextField(max_length=128,  blank=True, null=True, help_text='for github/gitlab imports')
    ssh_private_key = models.TextField(blank=True, null=True, help_text='for cloning private repos')
    ssh_unlock_passphrase = models.TextField(blank=True, null=True, help_text='for cloning private repos')
    description = models.TextField(max_length=128, blank=True, null=True)
    organization_identifier = models.CharField(max_length=256, blank=True, null=True, help_text='for github/gitlab imports')
    import_filter = models.CharField(max_length=256, blank=True, null=True, help_text='if set, only import repos matching this fnmatch pattern')
    api_endpoint = models.TextField(blank=True, null=True, help_text="for github/gitlab imports off private instances")

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



    organization = models.ForeignKey(Organization, db_index=True, on_delete=models.SET_NULL, null=True)
    enabled = models.BooleanField(default=True, help_text='if false, disable scanning')
    last_scanned = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField('Tag', related_name='tags', blank=True)
    last_pulled = models.DateTimeField(blank = True, null = True)
    url = models.TextField(max_length=255, db_index=True, blank=False, help_text='use a git ssh url for private repos, else http/s are ok')
    name = models.TextField(db_index=True, max_length=32, blank=False, null=False, validators=[validate_repo_name])
    color = models.CharField(max_length=10, null=True, blank=True)
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

    def effective_color(self):
        if self.color:
            return self.color
        return "#000000"

    def earliest_commit_date(self, author=None):

        commits = Commit.objects
        if author:
            commits = commits.filter(author=author)
        else:
            commits = commits.filter(author=author, repo=self)
        if commits.count():
            return commits.earliest("commit_date").commit_date
        return None

    def latest_commit_date(self, author=None):

        commits = Commit.objects
        if author:
            commits = commits.filter(author=author)
        else:
            commits = commits.filter(author=author, repo=self)
        if commits.count():
            return commits.latest("commit_date").commit_date
        return None

class Author(models.Model):
    email = models.TextField(db_index=True, max_length=64, unique=True, blank=False, null=True)

    def __str__(self):
        return f"Author: {self.email}"



class Tag(models.Model):
    name = models.TextField(max_length=64, db_index=True, blank=True, null=True)
    repos = models.ManyToManyField(Repository, related_name='+', blank=True)

    def __str__(self):
        return f"Tag: {self.name}"


class Commit(models.Model):

    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, related_name='commits')
    author = models.ForeignKey(Author, db_index=True, on_delete=models.CASCADE, blank=False, null=True, related_name='commits')
    sha = models.TextField(db_index=True, max_length=256, blank=False)
    commit_date = models.DateTimeField(db_index=True,blank=False, null=True)
    author_date = models.DateTimeField(blank=False, null=True)
    subject = models.TextField(db_index=True, max_length=256, blank=False)

    class Meta:
        unique_together = [ 'repo', 'sha' ]
        indexes = [
            models.Index(fields=['commit_date', 'author', 'repo']),
            models.Index(fields=['author_date', 'author', 'repo']),

        ]

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

    def __str__(self):
        return f"File: ({self.repo}) {self.path}/{self.name})"

class FileChange(models.Model):

    file = models.ForeignKey(File, db_index=True, on_delete=models.CASCADE, related_name='+', null=False)
    commit = models.ForeignKey(Commit, db_index=True, on_delete=models.CASCADE, related_name='file_changes')
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    class Meta:
        unique_together = [ 'file', 'commit' ]

    def __str__(self):
        return f"FileChange: {self.file.path} (c:{commit.sha})"


# if author = null, entry represents total stats for interval
# if author = X, entry represent X's author stats for the given interval

class Statistic(models.Model):

    INTERVALS = (
        ('DY', 'Day'),
        ('WK', 'Week'),
        ('MN', 'Month')
    )
    ATTRIBUTES = (
        ('commit_total', "Total Commits"),
        ('lines_added', "Lines Added"),
        ('lines_removed', "Lines Removed"),
        ('lines_changed', "Lines Changed"),
        ('files_changed', "Files Changed"),
        ('author_total', "Total Authors"),
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
            models.Index(fields=['start_date', 'interval', 'repo', 'author'], name='author_rollup'),
        ]

    @classmethod
    def create_file_rollup(cls, start_date, interval, repo, file, data):
        instance = cls(start_date = start_date, interval = interval, repo = repo, file = file, data = data)
        return instance

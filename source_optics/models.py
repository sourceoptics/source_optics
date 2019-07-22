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

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.postgres.indexes import BrinIndex
from django.contrib.auth.models import Group, User
from django import forms

# FIXME: remove non-database behavior from this module
import binascii
from django.conf import settings
import tempfile
import os
import subprocess
from source_optics.scanner.encrypt import SecretsManager


class Organization(models.Model):

    # parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    name = models.TextField(max_length=32, blank=False, unique=True)
    admins = models.ManyToManyField(User, related_name='+', help_text='currently unused')
    members = models.ManyToManyField(User, related_name='+', help_text='currently unused')

    credential = models.ForeignKey('Credential', on_delete=models.SET_NULL, null=True, help_text='used for repo imports and git checkouts')

    def __str__(self):
        return self.name

class Credential(models.Model):

    name = models.TextField(max_length=64, blank=False)
    username = models.TextField(max_length=32, blank=True, help_text='github/gitlab username')
    password = models.TextField(max_length=128,  blank=True, null=True, help_text='github/gitlab password (if using API imports)')
    ssh_private_key = models.TextField(blank=True, null=True, help_text='for cloning private repos')
    ssh_unlock_passphrase = models.TextField(blank=True, null=True, help_text='for cloning private repos')
    description = models.TextField(max_length=128, blank=True, null=True)
    api_endpoint = models.TextField(blank=True, null=True, help_text="optional git hosting API endpoint for import commands")

    class Meta:
        verbose_name = 'Credential'
        verbose_name_plural = 'Credentials'

    def __str__(self):
        return self.name

    # encrypt the password when we save this
    #  (password needs to be unencrypted when saved)

    def save(self, *args, **kwargs):
        mgr = SecretsManager()
        self.password = mgr.cloak(self.password)
        self.ssh_private_key = mgr.cloak(self.ssh_private_key)
        self.ssh_unlock_passphrase = mgr.cloak(self.ssh_unlock_passphrase)
        super().save(*args, **kwargs)

    def is_password(self):
        """
        Is this credential password based?  Prefer the key if available.
        """
        if not self.ssh_private_key and password:
            return True
        return False

    def is_keyfile(self):
        """
        Is this credential SSH-key based?  Prefer this over any password.
        ssh_agent.py can handle unlock passphrases and SSH agent support.
        See also INSTALL.md
        """
        if self.ssh_private_key:
            return True
        return False

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

    class Meta:
        verbose_name_plural = "repositories"
        
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    enabled = models.BooleanField(default=True, help_text='if false, disable scanning')
    last_scanned = models.DateTimeField(blank=True, null=True)
    last_rollup = models.DateTimeField(blank=True, null=True)
    earliest_commit = models.DateTimeField(blank=True, null=True)
    tags = models.ManyToManyField('Tag', related_name='tags', blank=True)
    last_pulled = models.DateTimeField(blank = True, null = True)
    url = models.TextField(max_length=256, unique=True, blank=False, help_text='use a git ssh url for private repos, else http/s are ok')
    name = models.TextField(db_index=True, max_length=32, blank=False, unique=True, null=False)
    color = models.CharField(max_length=10, null=True, blank=True)
    force_next_pull = models.BooleanField(null=False, default=False)

    def __str__(self):
        return self.name

    def effective_color(self):
        if self.color:
            return self.color
        return "#000000"


class Author(models.Model):
    email = models.TextField(db_index=True, max_length=64, unique=True, blank=False, null=True)
    repos = models.ManyToManyField(Repository, related_name='+')

    def __str__(self):
        return self.email

class Tag(models.Model):
    name = models.TextField(max_length=64, db_index=True, blank=True, null=True)
    repos = models.ManyToManyField(Repository, related_name='+', blank=True)

    def __str__(self):
        return self.name


class Commit(models.Model):
    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, related_name='commits')
    author = models.ForeignKey(Author, db_index=True, on_delete=models.CASCADE, blank=False, null=True, related_name='commits')
    sha = models.TextField(db_index=True, max_length=256, blank=False)
    files = models.ManyToManyField('File')
    commit_date = models.DateTimeField(db_index=True,blank=False, null=True)
    author_date = models.DateTimeField(blank=False, null=True)
    subject = models.TextField(db_index=True, max_length=256, blank=False)
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['commit_date', 'author', 'repo']),
        ]

    def __str__(self):
        return self.subject

class FileChange(models.Model):
    name = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    path = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    ext = models.TextField(max_length=32, blank=False)
    binary = models.BooleanField(default=False)
    commit = models.ForeignKey(Commit, db_index=True, on_delete=models.CASCADE, related_name='commit')
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='+', null=True)
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    def __str__(self):
        return self.path

class File(models.Model):
    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, related_name='+', null=True)
    name = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    path = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    ext = models.TextField(max_length=32, blank=False, null=True)
    binary = models.BooleanField(default=False)
    changes = models.ManyToManyField(FileChange, related_name='+')
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)


    indexes = [
        models.Index(fields=['repo', 'name', 'path', 'ext'], name='file_index'),
    ]

    def __str__(self):
        return self.path

# if author = null && file = null, entry represents total stats for interval
# if author = null && file = X, entry represents X's file stats for the given interval
# if author = X && file = null, entry represent X's author stats for the given interval

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
        
    start_date = models.DateTimeField(db_index=True, blank=False, null=True)
    interval = models.TextField(db_index=True, max_length=5, choices=INTERVALS)
    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, null=True, related_name='repo')
    author = models.ForeignKey(Author, db_index=True, on_delete=models.CASCADE, blank=True, null=True, related_name='author')
    file = models.ForeignKey(File, on_delete=models.CASCADE, blank=True, null=True, related_name='file')
    lines_added = models.IntegerField(blank = True, null = True)
    lines_removed = models.IntegerField(blank = True, null = True)
    lines_changed = models.IntegerField(blank = True, null = True)
    commit_total = models.IntegerField(blank = True, null = True)
    files_changed = models.IntegerField(blank = True, null = True)
    author_total = models.IntegerField(blank = True, null = True)

    def __str__(self):
        if self.author is None:
            return "TOTAL " + str(self.interval[0]) + " " + str(self.start_date.date())
        else:
            return "AUTHOR: " + str(self.author) + " " + str(self.interval[0]) + " " + str(self.start_date.date())

    class Meta:

        unique_together = [
            [ 'start_date', 'interval', 'repo', 'author', 'file' ]
        ]

        indexes = [
            models.Index(fields=['interval', 'author', 'repo', 'file', 'start_date'], name="rollup1"),
            models.Index(fields=['start_date', 'interval', 'repo', 'author'], name='author_rollup'),
        ]

    @classmethod
    def create_file_rollup(cls, start_date, interval, repo, file, data):
        instance = cls(start_date = start_date, interval = interval, repo = repo, file = file, data = data)
        return instance

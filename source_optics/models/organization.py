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

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

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
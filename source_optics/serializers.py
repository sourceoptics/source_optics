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

from django.contrib.auth.models import Group, User
from rest_framework import serializers

from .models import (Author, Commit, Credential, Organization, Repository,
                     Statistic)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class RepositorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Repository
        fields = ('organization', 'enabled', 'last_scanned', 'last_rollup', 'earliest_commit', 'tags', 'last_pulled', 'cred', 'url', 'name', 'color')

class CredentialSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Credential
        fields = ('name', 'username', 'description')

class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Organization
        fields = ('name', 'admins', 'members')

class AuthorSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Author
        fields = ('email', 'repos')

class CommitSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Commit
        fields = ('repo', 'author', 'sha', 'commit_date', 'author_date', 'subject',
                  'lines_added', 'lines_removed')

class StatisticSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Statistic
        fields = ('start_date', 'interval', 'repo', 'author', 'lines_added',
                  'lines_removed', 'lines_changed', 'commit_total', 'author_total')

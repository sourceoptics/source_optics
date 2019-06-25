from django.contrib.auth.models import User, Group
from rest_framework import serializers
from . models import Repository, Organization, LoginCredential, Author, Commit, Statistic

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
        model = LoginCredential
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


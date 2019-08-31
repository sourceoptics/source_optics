# contributor note: the django UI will be eventually replaced by a new dynamic frontend speaking to the REST API, do not add features

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

import traceback
from urllib.parse import parse_qs
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from django_tables2 import RequestConfig
from rest_framework import viewsets
from django.contrib.auth.models import User, Group
from source_optics.models import Repository, Organization, Credential, Commit, Author, Statistic
from source_optics.serializers import (AuthorSerializer, CommitSerializer,
                                       CredentialSerializer, GroupSerializer,
                                       OrganizationSerializer, RepositorySerializer,
                                       StatisticSerializer, UserSerializer)
from source_optics.views.webhooks import Webhooks
import datetime
from django.db.models import Sum, Max, Value, IntegerField, F
from django.db.models.expressions import Subquery, OuterRef
from . import dataframes
from . import graphs
import json

#=====
# BEGIN REST API

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    filter_backends = (DjangoFilterBackend,)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = (DjangoFilterBackend,)


class RepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name', 'url', 'tags', 'last_scanned', 'enabled', 'organization')


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class CredentialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name', 'username')


class CommitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Commit.objects.all()
    serializer_class = CommitSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
    'repo', 'author', 'sha', 'commit_date', 'author_date', 'subject', 'lines_added', 'lines_removed')


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('email', 'repos')


class StatisticViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Statistic.objects.all()
    serializer_class = StatisticSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('start_date', 'interval', 'repo', 'author', 'lines_added', 'lines_removed', 'lines_changed',
                        'commit_total', 'author_total')


# END REST API
# ======

def get_repo_table(repos, start, end):

    results = []
    for repo in repos:
        stat = Statistic.objects.order_by('repo__name').select_related('repository').filter(
            repo=repo,
            interval='DY',
            start_date__range=(start,end)
        ).aggregate(
            lines_changed=Sum('lines_changed'),
            lines_added=Sum('lines_added'),
            lines_removed=Sum('lines_removed'),
            author_total=Sum('author_total'),
            commit_total=Sum('commit_total')
        )
        stat['name'] = repo.name
        stat['details'] = repo.pk

        results.append(stat)

    results = sorted(results, key=lambda x: x['name'])

    return json.dumps(results)


def _get_scope(request, org=None, repos=None, repo=None, start=None, end=None, interval=None, repo_table=False):

    """
    Get objects from the URL parameters
    """

    orgs = Organization.objects.all()

    if interval is None:
        interval='WK'

    if end is not None:
        end = datetime.datetime.strptime(end, "%Y-%m-%d")
    else:
        end = datetime.datetime.now()

    if start is None:
        start = end - datetime.timedelta(days=14)
    else:
        start =datetime.datetime.strptime(start, "%Y-%m-%d")

    if org and org != '_':
        org = Organization.objects.get(pk=int(org))

    if repos and org and repos != '_':
        repos = repos_filter.split(',')
        repos = Repository.objects.select_related('organization').filter(organization=org, repos__name__in=repos)
    elif repos and repos != '_':
        repos = Repository.objects.select_related('organization').filter(repos__name__in=repos_filter)
    elif org:
        repos = Repository.objects.select_related('organization').filter(organization=org)
    else:
        repos = Repository.objects.select_related('organization')

    if repo:
        repo = Repository.objects.get(pk=repo)

    context = dict(
        orgs  = orgs.order_by('name').all(),
        org   = org,
        repos = repos.all(),
        start = start,
        end   = end,
        start_str = start.strftime("%Y-%m-%d"),
        end_str   = end.strftime("%Y-%m-%d"),
        repo = repo,
        intv = interval
    )

    if repo_table:
        context['repo_table'] = get_repo_table(repos, start, end)

    return (context, repo, start, end)

def _render_graph(request, org=None, repo=None, start=None, end=None, by_author=False, data_method=None, interval=None, graph_method=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    dataframe = getattr(dataframes, data_method)(repo=repo, start=start, by_author=by_author, end=end, interval=interval)
    scope['graph'] = getattr(graphs, graph_method)(repo=repo, start=start, end=end, df=dataframe)
    return render(request, 'graph.html', context=scope)

def repo(request, org=None, repo=None, start=None, end=None, intv=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end, interval=intv)
    return render(request, 'repo.html', context=scope)

def graph_volume(request, org=None, repo=None, start=None, end=None, intv=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval=intv,
        data_method='stat_series', graph_method='volume')

def graph_frequency(request, org=None, repo=None, start=None, end=None, intv=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval=intv,
        data_method='stat_series', graph_method='frequency')

def graph_participation(request, org=None, repo=None, start=None, end=None, intv=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval=intv,
        data_method='stat_series', graph_method='participation')

def graph_largest_contributors(request, org=None, repo=None, start=None, end=None, intv=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, by_author=True, interval=intv,
        data_method='stat_series', graph_method='largest_contributors')

def graph_granularity(request, org=None, repo=None, start=None, end=None, intv=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval=intv,
        data_method='stat_series', graph_method='granularity')

def graph_key_retention(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval='LF', by_author=True,
        data_method='stat_series', graph_method='key_retention')

def graph_early_retention(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval='LF', by_author=True,
        data_method='stat_series', graph_method='early_retention')

def graph_staying_power(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval='LF', by_author=True,
        data_method='stat_series', graph_method='staying_power')

def report_largest_contributors(request, org=None, repo=None, start=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)

    # FIXME: TODO: may want to take the limit as a parameter to the URL
    data = dataframes.stat_series(repo, start=start, end=end, by_author=True, interval='DY', want_dataframe=False)
    scope['author_json'] = json.dumps(data)
    return render(request, 'authors.html', context=scope)


def repos(request, org=None, repos=None, start=None, end=None, intv=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repos=repos, start=start, end=end, repo_table=True, interval=intv)
    return render(request, 'repos.html', context=scope)

def orgs(request):
    (scope, repo, start, end) = _get_scope(request)
    return render(request, 'orgs.html', context=scope)


@csrf_exempt
def webhook_post(request, *args, **kwargs):
    """
    Receive an incoming webhook and potentially trigger a build using
    the code in webhooks.py
    """

    if request.method != 'POST':
        return redirect('index')

    try:
        query = parse_qs(request.META['QUERY_STRING'])
        token = query.get('token', None)
        if token is not None:
            token = token[0]
        Webhooks(request, token).handle()
    except Exception:
        traceback.print_exc()
        # LOG.error("error processing webhook: %s" % str(e))
        return HttpResponseServerError("webhook processing error")

    return HttpResponse("ok", content_type="text/plain")


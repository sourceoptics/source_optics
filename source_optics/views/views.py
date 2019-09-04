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

# views.py - code immediately behind all of the web routes.  Renders pages, graphs, and charts.

import datetime
import json
import traceback
from urllib.parse import parse_qs

from django.contrib.auth.models import Group, User
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from source_optics.models import (Author, Commit, Credential,
                                  Organization, Repository, Statistic)
from source_optics.serializers import (AuthorSerializer, CommitSerializer,
                                       CredentialSerializer, GroupSerializer,
                                       OrganizationSerializer,
                                       RepositorySerializer,
                                       StatisticSerializer, UserSerializer)
from source_optics.views.webhooks import Webhooks
import source_optics.models as models
from . import dataframes, graphs
import altair as alt
import numpy as np
import pandas as pd

#=====
# BEGIN REST API
# FIXME: move this into a different file + make sure all fields are up to date

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


# FIXME: all the current statistic fields aren't here, we should read this from the Statistic model
# so we don't forget when adding new fields
class StatisticViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Statistic.objects.all()
    serializer_class = StatisticSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('start_date', 'interval', 'repo', 'author', 'lines_added', 'lines_removed', 'lines_changed',
                        'commit_total', 'author_total')


# END REST API
# ======

# FIXME: move these into another file, like 'tables.py'

def get_author_table(repo, start=None, end=None, interval=None, limit=None):
    """
    this drives the author tables, both ranged and non-ranged, accessed off the main repo list.
    the interval 'LF' shows lifetime stats, but elsewhere we just do daily roundups, so this parameter
    should really be a boolean.  The limit parameter is not yet used.
    """

    results = []

    authors = Author.authors(repo, start, end)

    for author in authors:
        if interval == 'LF':
            # we don't use aggregate
            # FIXME: this should be a function on the statistic object
            stats =  Statistic.queryset_for_range(repo, 'LF', author=author)
            if stats.count():
                # this IF is just in case there's an author row and we didn't do a full scan with the new code yet
                stat = stats.first()
                # FIXME: this is expensive, if we can get this data in one query and interlace the stat it will be MUCH faster
                stat2 = stat.to_author_dict(repo, author)
                results.append(stat2)

        else:
            # interval here as a parameter uses anything but lifetime as 'not lifetime', because this is just a table and not graphs
            stat1 = Statistic.queryset_for_range(repo, author=author, start=start, end=end, interval='DY')
            stat2 = Statistic.compute_interval_statistic(stat1, interval='DY', repo=repo, author=author, start=start, end=end)
            stat2 = stat2.to_dict()
            stat2['author'] = author.email
            results.append(stat2)
    return results


def get_repo_table(repos, start, end):

    """
    this drives the list of all repos within an organization, showing the statistics for them within the selected
    time range, along with navigation links.
    """

    results = []
    for repo in repos:
        # FIXME: REFACTOR: most of this entire block should use a method on Statistic

        stats = Statistic.queryset_for_range(repo, author=None, interval='DY', start=start, end=end)
        stat2 = Statistic.compute_interval_statistic(stats, interval='DY', repo=repo, author=None, start=start, end=end)
        stat2 = stat2.to_dict()
        stat2['name'] = repo.name
        # providing pk's for link columns in the repo chart
        for x in [ 'details1', 'details2', 'details3']:
            stat2[x] = repo.pk

        results.append(stat2)

    results = sorted(results, key=lambda x: x['name'])

    return json.dumps(results)


def _get_scope(request, org=None, repos=None, repo=None, start=None, end=None, interval=None, repo_table=False):

    models.cache_clear()

    """
    Get objects from the URL parameters.
    """

    orgs = Organization.objects.all()

    if interval is None:
        interval='WK'

    if end == '_':
        end = None
    elif end is not None:
        end = datetime.datetime.strptime(end, "%Y-%m-%d")
    else:
        end = timezone.now()

    if start == '_':
        start = None
    elif start is None:
        # FIXME: (minor) flip this if condition so it looks like the above method
        start = end - datetime.timedelta(days=14)
    else:
        start = datetime.datetime.strptime(start, "%Y-%m-%d")

    if org and org != '_':
        org = Organization.objects.get(pk=int(org))

    # FIXME: this should probably be a method on Repository
    if repos and org and repos != '_':
        repos = repos.split(',')
        repos = Repository.objects.select_related('organization').filter(organization=org, repos__name__in=repos)
    elif repos and repos != '_':
        repos = Repository.objects.select_related('organization').filter(repos__name__in=repos)
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
        repo = repo,
        intv = interval,
        title = "Source Optics"
    )

    if start and end:
        context['start_str'] = start.strftime("%Y-%m-%d")
        context['end_str'] = end.strftime("%Y-%m-%d")
    else:
        context['start_str'] = None
        context['end_str'] = None

    if repo_table:
        context['repo_table'] = get_repo_table(repos, start, end)

    return (context, repo, start, end)

# FIXME: way too much duplication here, make this nice

def _render_graph(request, org=None, repo=None, start=None, end=None, by_author=False, data_method=None,
                  interval=None, graph_method=None, limit_top_authors=False):
    """
    a helper method used by all the Statistic-based graph rendering view functions.
    """
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    if by_author and limit_top_authors:
        # FIXME: a bit of a mess here, but not all data frame methods take this parameter
        dataframe = getattr(dataframes, data_method)(repo=repo, start=start, by_author=by_author, end=end, interval=interval, limit_top_authors=True)
    else:
        dataframe = getattr(dataframes, data_method)(repo=repo, start=start, by_author=by_author, end=end, interval=interval)
    scope['graph'] = getattr(graphs, graph_method)(repo=repo, start=start, end=end, df=dataframe)
    return render(request, 'graph.html', context=scope)

def repo(request, org=None, repo=None, start=None, end=None, intv=None):
    """
    Generates the index page for a given repo.
    The index page is mostly a collection of graphs, so perhaps it should be called repo_graphs.html and this method
    should also be renamed.
    """
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end, interval=intv)
    scope['title'] = "Source Optics: %s repo (graphs)" % repo.name
    return render(request, 'repo.html', context=scope)

def graph_volume(request, org=None, repo=None, start=None, end=None, intv=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval=intv)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='day', y='lines_changed', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_frequency(request, org=None, repo=None, start=None, end=None, intv=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval=intv)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='day', y='commit_total', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_participation(request, org=None, repo=None, start=None, end=None, intv=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval=intv)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='day', y='author_total', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_largest_contributors(request, org=None, repo=None, start=None, end=None, intv=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval=intv, by_author=True, limit_top_authors=True)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='day', y='commit_total', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_granularity(request, org=None, repo=None, start=None, end=None, intv=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval=intv)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='day', y='average_commit_size', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_key_retention(request, org=None, repo=None, start=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval='LF', by_author=True)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='earliest_commit_day', y='longevity', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_files_time(request, org=None, repo=None, start=None, intv=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval=intv, by_author=True)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='day', y='files_changed', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_bias_time(request, org=None, repo=None, start=None, intv=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval=intv)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='day', y='bias', fit=True)
    return render(request, 'graph.html', context=scope)


def graph_commitment(request, org=None, repo=None, start=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval='LF', by_author=True)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='earliest_commit_day', y='commitment', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_early_retention(request, org=None, repo=None, start=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval='LF', by_author=True)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='earliest_commit_day', y='commit_total', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_staying_power(request, org=None, repo=None, start=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval='LF', by_author=True)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='latest_commit_day', y='longevity', fit=True)
    return render(request, 'graph.html', context=scope)

def graph_bias_impact(request, org=None, repo=None, start=None, end=None):
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    df = dataframes.stat_series(repo, start=start, end=end, interval='LF', by_author=True)
    scope['graph'] = graphs.scatter_plot(repo=repo, start=start, end=end, df=df, x='bias', y='lines_changed', fit=True)
    return render(request, 'graph.html', context=scope)

def report_authors(request, org=None, repo=None, start=None, end=None, intv=None, limit=None):
    """
    generates a partial graph which is loaded in the repo graphs page. more comments in graphs.py
    """
    (scope, repo, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end, interval=intv)
    data = get_author_table(repo, start=start, end=end, interval=intv, limit=limit)
    scope['title'] = "Source Optics: %s repo: (authors report)" % repo.name
    scope['author_json'] = json.dumps(data)
    return render(request, 'authors.html', context=scope)

def repos(request, org=None, repos=None, start=None, end=None, intv=None):
    """
    generates the list of all repos, with stats and navigation.
    """
    (scope, repo, start, end) = _get_scope(request, org=org, repos=repos, start=start, end=end, repo_table=True, interval=intv)
    org = Organization.objects.get(pk=org)
    scope['title'] = "Source Optics: %s organization" % org.name
    return render(request, 'repos.html', context=scope)

def orgs(request):
    """
    the index page for the app, presently, lists all organizations.  This should be morphed to a generic dashboard
    that also lists the orgs.
    """
    (scope, repo, start, end) = _get_scope(request)
    scope['title'] = "Source Optics: index"
    return render(request, 'orgs.html', context=scope)


@csrf_exempt
def webhook_post(request, *args, **kwargs):
    """
    Receive an incoming webhook from something like GitHub and potentially flag a source code repo for a future scan,
    using the code in webhooks.py
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
        return HttpResponseServerError("webhook processing error")

    return HttpResponse("ok", content_type="text/plain")

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
from . import dataframes, reports
from . import graphs as graph_module
from .scope import Scope


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
    filterset_fields = ('repo', 'author', 'sha', 'commit_date', 'author_date', 'subject')


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('email',)

# FIXME: all the current statistic fields aren't here, we should read this from the Statistic model
# so we don't forget when adding new fields
class StatisticViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Statistic.objects.all()
    serializer_class = StatisticSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('start_date', 'interval', 'repo', 'author')


# END REST API
# ======

# FIXME: move these into another file, like 'tables.py'




def graphs(request):
    """
    Generates a page full of graphs that is relatively context sensitive based on the query string
    """
    scope = Scope(request)
    assert scope.repo is not None
    scope.context['title'] = "Source Optics: %s repo (graphs)" % scope.repo.name
    return render(request, 'graphs.html', context=scope.context)

def graph_participation(request):
    scope = Scope(request)
    df = dataframes.team_time_series(scope)
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='author_total')
    return render(request, 'graph.html', context=scope.context)

def graph_files_changed(request):
    scope = Scope(request)
    df = dataframes.team_time_series(scope)
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='files_changed')
    return render(request, 'graph.html', context=scope.context)

def graph_lines_changed(request):
    scope = Scope(request)
    (df, top) = dataframes.top_author_time_series(scope, aspect='lines_changed')
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='lines_changed', top=top, by_author=True, aspect='commit_total')
    return render(request, 'graph.html', context=scope.context)

def graph_commits(request):
    scope = Scope(request)
    (df, top) = dataframes.top_author_time_series(scope, aspect='commit_total')
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='commit_total', top=top, by_author=True, aspect='commit_total')
    return render(request, 'graph.html', context=scope.context)

def graph_creates(request):
    scope = Scope(request)
    (df, top) = dataframes.top_author_time_series(scope, aspect='commit_total')
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='creates', top=top, by_author=True, aspect='commit_total')
    return render(request, 'graph.html', context=scope.context)

def graph_edits(request):
    # FIXME: DRY on all of these
    scope = Scope(request)
    (df, top) = dataframes.top_author_time_series(scope, aspect='commit_total')
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='edits', top=top, by_author=True, aspect='commit_total')
    return render(request, 'graph.html', context=scope.context)

def graph_moves(request):
    scope = Scope(request)
    (df, top) = dataframes.top_author_time_series(scope, aspect='commit_total')
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='moves', top=top, by_author=True, aspect='commit_total')
    return render(request, 'graph.html', context=scope.context)

def graph_commit_size(request):
    scope = Scope(request)
    df = dataframes.team_time_series(scope)
    scope.context['graph'] = graph_module.time_plot(df=df, scope=scope, y='average_commit_size')
    return render(request, 'graph.html', context=scope.context)

def report_author_stats(request):
    """
    generates a partial graph which is loaded in the repo graphs page. more comments in graphs.py
    """
    limit = None
    scope = Scope(request)
    data = reports.author_stats_table(scope, limit=limit)
    if scope.repo:
        # FIXME: this should be done in the template
        scope.context['title'] = "Source Optics: stats for repo=%s" % scope.repo.name
    else:
        scope.context['title'] = "Source Optics: stats for author=%s" % scope.author.email

    scope.context['author_count'] = len(data)
    scope.context['table_json'] = json.dumps(data)
    # FIXME: should be repo_authors ? perhaps this will be standardized...
    return render(request, 'author_stats.html', context=scope.context)

def report_commits(request, org=None):
    # FIXME: how about a scope object?
    scope = Scope(request)
    data = reports.commits_feed(scope)
    assert scope.repo or scope.author
    # FIXME: this needs cleanup - move generic pagination support to a common function
    # TODO: title can come from commits_feed function
    scope.context['title'] = "Source Optics: commit feed"
    scope.context['table_json'] = json.dumps(data['results'])
    page = data['page']
    scope.context['page_number'] = page.number
    scope.context['has_previous'] = page.has_previous()
    if scope.context['has_previous']:
        if scope.repo:
            scope.context['next_link'] = "/report/commits?repo=%s&start=%s&end=%s&page=%s" % (scope.repo.pk, scope.start_str, scope.end_str, page.next_page_number())
        elif scope.author:
            scope.context['next_link'] = "/report/commits?author=%s&start=%s&end=%s&page=%s" % (scope.author.pk, scope.start_str, scope.end_str, page.next_page_number())
    scope.context['has_next'] = page.has_next()
    if scope.context['has_next']:
        if scope.repo:
            scope.context['next_link'] = "/report/commits?repo=%s&start=%s&end=%s&page=%s" % (scope.repo.pk, scope.start_str, scope.end_str, page.next_page_number())
        elif scope.author:
            scope.context['next_link'] = "/report/commits?author=%s&start=%s&end=%s&page=%s" % (scope.author.pk, scope.start_str, scope.end_str, page.next_page_number())
    scope.context.update(data)
    return render(request, 'commits.html', context=scope.context)

def repos(request, org=None):
    """
    generates the list of all repos, with stats and navigation.
    """
    scope = Scope(request, org=org, add_repo_table=True)
    scope.context['title'] = "Source Optics: %s organization" % scope.org.name
    return render(request, 'repos.html', context=scope.context)

def orgs(request):
    """
    the index page for the app, presently, lists all organizations.  This should be morphed to a generic dashboard
    that also lists the orgs.
    """
    scope = Scope(request, add_orgs_table=True)
    scope.context['title'] = "Source Optics: index"
    return render(request, 'orgs.html', context=scope.context)


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

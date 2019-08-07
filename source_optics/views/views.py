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
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from . graphs.generate import GraphGenerator
from ..models import Repository, Organization, Credential, Commit, Author, Statistic
from ..serializers import (AuthorSerializer, CommitSerializer,
                           CredentialSerializer, GroupSerializer,
                           OrganizationSerializer, RepositorySerializer,
                           StatisticSerializer, UserSerializer)
from . import v1_graph, v1_util
from .v1_tables import StatTable, AuthorStatTable
from .webhooks import Webhooks


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
    filterset_fields = ('name', 'url', 'cred', 'tags', 'earliest_commit', 'last_scanned', 'enabled', 'organization')

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
    filterset_fields = ('repo', 'author', 'sha', 'commit_date', 'author_date', 'subject', 'lines_added', 'lines_removed')

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

def index(request):
    """
    Site homepage lists all repos (or all repos in an organization)
    """

    org = request.GET.get('org')
    repos = v1_util.query(request.GET.get('filter'), org)
    queries = v1_util.get_query_strings(request)

    # aggregates statistics for repositories based on start and end date
    stats = v1_util.get_all_repo_stats(repos=repos, start=queries['start'], end=queries['end'])
    stat_table = StatTable(stats)

    # FIXME: make pagination configurable
    RequestConfig(request, paginate={'per_page': 100 }).configure(stat_table)

    context = {
        'title': 'SrcOptics',
        'organizations': Organization.objects.all(),
        'repositories': repos,
        'stats': stat_table
    }

    return render(request, 'dashboard.html', context=context)


"""
Data to be displayed for the repo details view
"""

# FIXME: not all of the code is needed for each (author elements vs line_elements?), simplify this later

def repo_team(request, repo_name):
    return _repo_details(request, repo_name, template='repo_team.html')

def repo_contributors(request, repo_name):
    return _repo_details(request, repo_name, template='repo_contributors.html')

def _repo_details(request, repo_name, template=None):
    
    assert template is not None

    #Gets repo name from url slug
    repo = Repository.objects.get(name=repo_name)

    queries = v1_util.get_query_strings(request)

    stats = v1_util.get_all_repo_stats(repos=[repo], start=queries['start'], end=queries['end'])

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    #Generates line graphs based on attribute query param
    # FIXME: take the object, not the name
    line_elements = v1_graph.attribute_graphs(request, repo_name)

    #Generates line graph of an attribute for the top contributors
    # to that attribute within the specified time period
    # FIXME: take the object, not the name
    author_elements = v1_graph.attribute_author_graphs(request, repo_name)

    #possible attribute values to filter by
    attributes = Statistic.ATTRIBUTES

    #possible interval values to filter by
    intervals = Statistic.INTERVALS

    # Get the attribute to get the top authors for from the query parameter
    attribute = request.GET.get('attr')

    if not attribute:
        attribute = attributes[0][0]

    # Generate a table of the top contributors statistics
    authors = v1_util.get_top_authors(repo=repo, start=queries['start'], end=queries['end'], attribute=queries['attribute'])
    author_stats = v1_util.get_all_author_stats(authors=authors, repo=repo, start=queries['start'], end=queries['end'])
    author_table = AuthorStatTable(author_stats)
    RequestConfig(request, paginate={'per_page': 6}).configure(author_table)

    summary_stats = v1_util.get_lifetime_stats(repo)

    #Context variable being passed to template
    context = {
        'repo': repo,
        'stats': stat_table,
        'summary_stats': summary_stats,
        'data': line_elements,
        'author_graphs': author_elements,
        'author_table': author_table,
        'attributes': attributes,
        'intervals':intervals
    }
    return render(request, template, context=context)


"""
Data to be displayed for the author details view
"""
def author_details(request, author_email):
    #Gets repo name from url slug
    auth = Author.objects.get(email=author_email)

    queries = v1_util.get_query_strings(request)

    stats = v1_util.get_total_author_stats(author=auth, start=queries['start'], end=queries['end'])

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 5}).configure(stat_table)

    #Generates line graphs based on attribute query param
    line_elements = v1_graph.attribute_summary_graph_author(request, auth)

    # get the top repositories the author commits to
    author_elements = v1_graph.attribute_author_contributions(request, auth)

    #possible attribute values to filter by
    attributes = Statistic.ATTRIBUTES

    #possible interval values to filter by
    intervals = Statistic.INTERVALS

    # Get the attribute to get the top authors for from the query parameter
    attribute = request.GET.get('attr')

    if not attribute:
        attribute = attributes[0][0]

    # Generate a table of the top contributors statistics
    #authors = util.get_top_authors(repo=repo, start=queries['start'], end=queries['end'], attribute=queries['attribute'])
    #author_stats = util.get_all_author_stats(authors=authors, repo=repo, start=queries['start'], end=queries['end'])
    #author_table = AuthorStatTable(author_stats)
    #RequestConfig(request, paginate={'per_page': 10}).configure(author_table)

    summary_stats = v1_util.get_lifetime_stats_author(auth)

    #Context variable being passed to template
    context = {
        'title': "Author Details: " + str(auth),
        'stats': stat_table,
        'summary_stats': summary_stats,
        'data': line_elements,
        'author_graphs': author_elements,
        'attributes': attributes,
        'intervals':intervals
    }
    return render(request, 'author_details.html', context=context)


def attributes_by_repo(request):

    
    data = v1_graph.attributes_by_repo(request)
    context = {
        'title': 'Repo Statistics Over Time',
        'organizations': Organization.objects.all(),
        'data' : data,
        'attributes': Statistic.ATTRIBUTES,
        'intervals': Statistic.INTERVALS,
        'repos': Repository.objects.all()
    }
    return render(request, 'repo_view.html', context=context)

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
        #LOG.error("error processing webhook: %s" % str(e))
        return HttpResponseServerError("webhook processing error")

    return HttpResponse("ok", content_type="text/plain")

@api_view(['POST'])
def generate_graph(request):
    """
    List all code snippets, or create a new snippet.
    """
    #data = request.data

    data = dict(
        end = "2004-10-06 10:00:00",
        days = 14,
        interval = "WK",
        organization_id = 1,
        repo_pattern = "%",
        plugin = "repo_summary"
    )

    if 'error' not in data:
        data = GraphGenerator(data).graph()
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

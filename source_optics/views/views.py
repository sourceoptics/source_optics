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
from django.db.models import Sum, Max, Value, IntegerField
from django.db.models.expressions import Subquery, OuterRef
from . import dataframes
from . import graphs

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


def _repo_stats(repos, start, end):

    # this generates 1 query per repo - which is *not* optimal, but will do for now.

    repos = repos.order_by('name').all()
    results = []

    for repo in repos:

        stat = Statistic.objects.filter(
            repo = repo,
            author__isnull=True,
            interval='DY',
            start_date__gte=start,
            start_date__lte=end
        ).aggregate(
            lines_added = Sum('lines_added'),
            lines_removed = Sum('lines_removed'),
            lines_changed = Sum('lines_changed'),
            author_total = Max('author_total'),
            commit_total=Sum("commit_total"),
            files_changed=Sum("files_changed"),
        )

        results.append(dict(
            id = repo.id,
            pk = repo.id,
            name = repo.name,
            lines_added = stat['lines_added'],
            lines_removed = stat['lines_removed'],
            lines_changed = stat['lines_changed'],
            author_total = stat['author_total'],
            commit_total = stat['commit_total'],
            files_changed = stat['files_changed']
        ))


    print("RESULTS=%s" % results)
    return results


def _get_scope(request, org=None, repos=None, repo=None, start=None, end=None, repo_stats=False):

    """
    Get objects from the URL parameters
    """

    orgs = Organization.objects.all()

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
        repo = repo
    )

    if repo_stats:
        context['stats'] = _repo_stats(repos, start, end)

    return (context, start, end)

def _render_graph(request, org=None, repo=None, start=None, end=None, by_author=False, data_method=None, interval=None, graph_method=None):
    (scope, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    dataframe = getattr(dataframes, data_method)(repo=repo, start=start, by_author=by_author, end=end, interval=interval)
    scope['graph'] = getattr(graphs, graph_method)(repo=repo, start=start, end=end, df=dataframe)
    return render(request, 'graph.html', context=scope)

def repo(request, org=None, repo=None, start=None, end=None):
    (scope, start, end) = _get_scope(request, org=org, repo=repo, start=start, end=end)
    return render(request, 'repo.html', context=scope)

SKETCH = """
def repo_total_graph(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, method='total_series')

def repo_author_graph(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, method='author_series')

def repo_health_matrix(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, method='health_matrix')
"""

def graph_volume(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end,
        data_method='stat_series', graph_method='volume')

def graph_frequency(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end,
        data_method='stat_series', graph_method='frequency')

def graph_participation(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, interval='MN',
        data_method='stat_series', graph_method='participation')

def graph_largest_contributors(request, org=None, repo=None, start=None, end=None):
    return _render_graph(request, org=org, repo=repo, start=start, end=end, by_author=True, interval='MN',
        data_method='stat_series', graph_method='largest_contributors')

def repos(request, org=None, repos=None, start=None, end=None):
    (scope, start, end) = _get_scope(request, org=org, repos=repos, start=start, end=end, repo_stats=True)
    return render(request, 'repos.html', context=scope)

def orgs(request):
    (scope, start, end) = _get_scope(request)
    return render(request, 'orgs.html', context=scope)



"""
Data to be displayed for the repo details view
"""


OLD = """
# FIXME: not all of the code is needed for each (author elements vs line_elements?), simplify this later

def v1_repo_team(request, repo_name):
    return _repo_details(request, repo_name, template='repo_team.html')


def v1_epo_contributors(request, repo_name):
    return _repo_details(request, repo_name, template='repo_contributors.html')


def v1_repo_details(request, repo_name, template=None):
    assert template is not None

    # Gets repo name from url slug
    repo = Repository.objects.get(name=repo_name)

    queries = v1_util.get_query_strings(request)

    stats = v1_util.get_all_repo_stats(repos=[repo], start=queries['start'], end=queries['end'])

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 10}).configure(stat_table)

    # Generates line graphs based on attribute query param
    # FIXME: take the object, not the name
    line_elements = v1_graph.attribute_graphs(request, repo_name)

    # Generates line graph of an attribute for the top contributors
    # to that attribute within the specified time period
    # FIXME: take the object, not the name
    author_elements = v1_graph.attribute_author_graphs(request, repo_name)

    # possible attribute values to filter by
    attributes = Statistic.ATTRIBUTES

    # possible interval values to filter by
    intervals = Statistic.INTERVALS

    # Get the attribute to get the top authors for from the query parameter
    attribute = request.GET.get('attr')

    if not attribute:
        attribute = attributes[0][0]

    # Generate a table of the top contributors statistics
    authors = v1_util.get_top_authors(repo=repo, start=queries['start'], end=queries['end'],
                                      attribute=queries['attribute'])
    author_stats = v1_util.get_all_author_stats(authors=authors, repo=repo, start=queries['start'], end=queries['end'])
    author_table = AuthorStatTable(author_stats)
    RequestConfig(request, paginate={'per_page': 6}).configure(author_table)

    summary_stats = v1_util.get_lifetime_stats(repo)

    # Context variable being passed to template
    context = {
        'repo': repo,
        'stats': stat_table,
        'summary_stats': summary_stats,
        'data': line_elements,
        'author_graphs': author_elements,
        'author_table': author_table,
        'attributes': attributes,
        'intervals': intervals
    }
    return render(request, template, context=context)



def v1_author_details(request, author_email):
    # Gets repo name from url slug
    auth = Author.objects.get(email=author_email)

    queries = v1_util.get_query_strings(request)

    stats = v1_util.get_total_author_stats(author=auth, start=queries['start'], end=queries['end'])

    stat_table = StatTable(stats)
    RequestConfig(request, paginate={'per_page': 5}).configure(stat_table)

    # Generates line graphs based on attribute query param
    line_elements = v1_graph.attribute_summary_graph_author(request, auth)

    # get the top repositories the author commits to
    author_elements = v1_graph.attribute_author_contributions(request, auth)

    # possible attribute values to filter by
    attributes = Statistic.ATTRIBUTES

    # possible interval values to filter by
    intervals = Statistic.INTERVALS

    # Get the attribute to get the top authors for from the query parameter
    attribute = request.GET.get('attr')

    if not attribute:
        attribute = attributes[0][0]

    # Generate a table of the top contributors statistics
    # authors = util.get_top_authors(repo=repo, start=queries['start'], end=queries['end'], attribute=queries['attribute'])
    # author_stats = util.get_all_author_stats(authors=authors, repo=repo, start=queries['start'], end=queries['end'])
    # author_table = AuthorStatTable(author_stats)
    # RequestConfig(request, paginate={'per_page': 10}).configure(author_table)

    summary_stats = v1_util.get_lifetime_stats_author(auth)

    # Context variable being passed to template
    context = {
        'title': "Author Details: " + str(auth),
        'stats': stat_table,
        'summary_stats': summary_stats,
        'data': line_elements,
        'author_graphs': author_elements,
        'attributes': attributes,
        'intervals': intervals
    }
    return render(request, 'author_details.html', context=context)

"""

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


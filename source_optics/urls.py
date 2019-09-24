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

from django.urls import include, path
from rest_framework import routers

from source_optics.views import views

api_router = router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'repositories', views.RepositoryViewSet)
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'credentials', views.CredentialViewSet)
router.register(r'author', views.AuthorViewSet)
router.register(r'statistic', views.StatisticViewSet)
router.register(r'commit', views.CommitViewSet)


urlpatterns = [

    # top level pages - object hierarchy navigation
    path('', views.orgs, name='orgs'),
    # FIXME: use org in query string, else show all repos
    path('org/<org>/repos', views.repos, name='repos'),
    path('author/<author>', views.author, name='author'),
    path('repo/<repo>', views.repo, name='repo'),

    # GRAPH snippets loaded from /graphs
    path('graph/participation', views.graph_participation, name='graph_participation'),
    path('graph/commits', views.graph_commits, name='graph_commits'),
    path('graph/lines_changed', views.graph_lines_changed, name='graph_lines_changed'),
    path('graph/files_changed', views.graph_files_changed, name='graph_files_changed'),
    path('graph/commit_size', views.graph_commit_size, name='graph_commit_size'),
    path('graph/creates', views.graph_creates, name='graph_creates'),
    path('graph/edits', views.graph_edits, name='graph_edits'),
    path('graph/moves', views.graph_moves, name='graph_moves'),

    # REPORTS AND GRAPH PAGES - RATHER FLEXIBLE BY QUERY STRING
    path('graphs', views.graphs, name='graphs'),
    path('report/stats', views.report_stats, name='report_author_stats'),
    path('report/commits', views.report_commits, name='report_commits'),
    path('report/files', views.report_files, name='report_files'),

    # REST API
    path('api/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Webhooks
    path('webhook', views.webhook_post, name='webhook_post'),
    path('webhook/', views.webhook_post, name='webhook_post'),

]

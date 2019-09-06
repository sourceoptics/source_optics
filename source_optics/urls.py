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

    # FIXME: move the app to use the django URL reversing function before changing URL structure.
    # FIXME: UI - these should all be changed to use query strings, work just needs to be done later.
    # FIXME: the org parameter is unneccessary when repo is specified.

    path('', views.orgs, name='orgs'),
    path('org/<org>/repos/<repos>/', views.repos, name='repos'),
    path('org/<org>/repo/<repo>/', views.repo, name='repo'),
    # TODO: use the reverse url function vs having these URLs directly in templates
    path('org/<org>/repo/<repo>/graph/volume', views.graph_volume, name='graph_volume'),
    path('org/<org>/repo/<repo>/graph/frequency', views.graph_frequency, name='graph_frequency'),
    path('org/<org>/repo/<repo>/graph/participation', views.graph_participation, name='graph_participation'),
    path('org/<org>/repo/<repo>/graph/frequent_contributors', views.graph_frequent_contributors, name='graph_frequent_contributors'),
    path('org/<org>/repo/<repo>/graph/largest_contributors', views.graph_largest_contributors, name='graph_largest_contributors'),
    path('org/<org>/repo/<repo>/graph/granularity', views.graph_granularity, name='graph_granularity'),
    path('org/<org>/repo/<repo>/graph/files_time', views.graph_files_time, name='graph_files_time'),

    path('org/<org>/repo/<repo>/report/authors', views.report_authors, name='report_authors'),

    # REST API
    path('api/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Webhooks
    path('webhook', views.webhook_post, name='webhook_post'),
    path('webhook/', views.webhook_post, name='webhook_post'),

]

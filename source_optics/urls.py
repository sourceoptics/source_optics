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

    # UI
    path('', views.orgs, name='orgs'),
    path('org/<org>/repos/<repos>/start/<start>/end/<end>/intv/<intv>', views.repos, name='repos'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/intv/<intv>', views.repo, name='repo'),
    # TODO: use the reverse url function vs having these URLs directly in templates
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/intv/<intv>/graph/volume', views.graph_volume, name='graph_volume'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/intv/<intv>/graph/frequency', views.graph_frequency, name='graph_frequency'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/intv/<intv>/graph/participation', views.graph_participation, name='graph_participation'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/intv/<intv>/graph/largest_contributors', views.graph_largest_contributors, name='graph_largest_contributors'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/intv/<intv>/graph/granularity', views.graph_granularity, name='graph_granularity'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/graph/key_retention', views.graph_key_retention, name='graph_key_retention'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/graph/early_retention', views.graph_early_retention, name='graph_early_retention'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/graph/staying_power', views.graph_staying_power, name='graph_staying_power'),
    path('org/<org>/repo/<repo>/start/<start>/end/<end>/intv/<intv>/report/largest_contributors', views.report_largest_contributors, name='report_largest_contributors'),

    # REST API
    path('api/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # OBSOLETE
    # path('report_api/', views.generate_graph),

    # Webhooks
    path('webhook', views.webhook_post, name='webhook_post'),
    path('webhook/', views.webhook_post, name='webhook_post'),

]

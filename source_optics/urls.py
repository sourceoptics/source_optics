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

from .views import views  # FIXME

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
    path('', views.index),

    # REST API
    path('api/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('report_api/', views.generate_graph),

    # Webhooks
    path('webhook', views.webhook_post, name='webhook_post'),
    path('webhook/', views.webhook_post, name='webhook_post'),

    # UI
    path('repos/', views.attributes_by_repo, name='repos'),
    path('repos/<repo_name>/team', views.repo_team, name='repo_team'),
    path('repos/<repo_name>/contributors', views.repo_contributors, name='repo_contributors'),
    path('author/<author_email>/', views.author_details, name='author_details')

]

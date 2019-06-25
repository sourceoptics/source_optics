from django.urls import path, include

from . views import views
from rest_framework import routers

api_router = router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'repositories', views.RepositoryViewSet)
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'credentials', views.CredentialViewSet)


urlpatterns = [

    # UI
    path('', views.index),

    # REST API
    path('api/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # UI
    path('repos/', views.attributes_by_repo, name='repos'),
    path('repos/<repo_name>/team', views.repo_team, name='repo_team'),
    path('repos/<repo_name>/contributors', views.repo_contributors, name='repo_contributors'),
    path('author/<author_email>/', views.author_details, name='author_details')

]

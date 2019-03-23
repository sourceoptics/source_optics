from django.urls import path, re_path

from . import views,graph

urlpatterns = [
    path('', views.index),
    # path('repo/<str:repo_name>', graph.basic),
    path('repos/', graph.commits_by_repo, name='repos'),
    re_path(r'^repo/.*$', views.index, name='index'),
]

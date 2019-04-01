from django.urls import path, re_path

from . import views, graph, api

urlpatterns = [
    path('', views.index),
    # path('repo/<str:repo_name>', graph.basic),
    path('repos/', graph.attributes_by_repo, name='repos'),
    # path('repo_details/', views.repo_details, name='repo_details'),
    path('repos/<slug>/', views.repo_details, name='repo_details'),
    path('q/<query>/', api.search, name='api')
]

from django.urls import path, re_path

from . import views, graph, util

urlpatterns = [
    path('', views.index),
    path('repos/', views.attributes_by_repo, name='repos'),

    path('repos/<repo_name>/team', views.repo_team, name='repo_team'),
    path('repos/<repo_name>/contributors', views.repo_contributors, name='repo_contributors'),

    path('author/<author_email>/', views.author_details, name='author_details'),
    

]

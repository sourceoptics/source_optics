from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('repo/', views.repo_selected, name='repo'),
]

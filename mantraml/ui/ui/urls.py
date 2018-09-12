from django.contrib import admin
from django.urls import path, include, re_path

from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('cloud/', views.cloud),
    path('datasets/', views.datasets),
    path('models/', views.models),
    path('trials/', views.trials),
    path('results/', views.results),
    path('data/<dataset_name>/', views.view_dataset, name='view_dataset'),
    path('data/<dataset_name>/<task_name>', views.view_dataset_task, name='view_dataset_task'),
    path('model/<model_name>/', views.view_model, name='view_model'),
    path('result/<result_folder>/', views.view_result, name='view_result'),
    path('result/<result_folder>/tensorboard', views.view_result_tensorboard, name='view_result_tensorboard'),
    path('trial/<trial_folder>/', views.view_trial, name='view_trial'),
    path('trial/<trial_folder>/tensorboard', views.view_trial_tensorboard, name='view_trial_tensorboard'),
    path('trials/<trial_group_folder>/', views.view_trial_group, name='view_trial_group'),
    re_path(r'^model/(?P<model_name>\w+)/tree/(?P<path>.*)$', views.view_model_codebase),
    re_path(r'^data/(?P<dataset_name>\w+)/tree/(?P<path>.*)$', views.view_dataset_codebase),
]

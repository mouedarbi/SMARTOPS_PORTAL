from django.urls import path
from . import views

app_name = 'smartops_plugin_map'

urlpatterns = [
    path('', views.map_index, name='index'),
]

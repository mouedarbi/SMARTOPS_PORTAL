"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration des routes pour le catalogue de modules.
"""

from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.module_list, name='module_list'),
    path('<slug:slug>/', views.module_detail, name='module_detail'),
]

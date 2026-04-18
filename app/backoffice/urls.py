"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : backoffice
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Routage des URLs pour l'administration personnalisée.
"""

from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.index, name='index'),
    path('modules/', views.module_list, name='module_list'),
    path('bundles/', views.bundle_list, name='bundle_list'),
    path('licenses/', views.license_list, name='license_list'),
]

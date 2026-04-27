"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : backoffice
Auteur : Mohamed Ouedarbi
Version : 4.0
Description : Routage complet du Backoffice (CoreVersions inclus).
"""

from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Gestion des Modules
    path('modules/', views.module_list, name='module_list'),
    path('modules/create/', views.module_create, name='module_create'),
    path('modules/<int:pk>/edit/', views.module_edit, name='module_edit'),
    path('modules/<int:pk>/delete/', views.module_delete, name='module_delete'),
    
    # Gestion des Catégories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Gestion des Versions Core
    path('core-versions/', views.core_version_list, name='core_version_list'),
    path('core-versions/create/', views.core_version_create, name='core_version_create'),
    path('core-versions/<int:pk>/edit/', views.core_version_edit, name='core_version_edit'),
    path('core-versions/<int:pk>/delete/', views.core_version_delete, name='core_version_delete'),

    # Gestion des Packs (Bundles)
    path('bundles/', views.bundle_list, name='bundle_list'),
    path('bundles/create/', views.bundle_create, name='bundle_create'),
    path('bundles/<int:pk>/edit/', views.bundle_edit, name='bundle_edit'),
    path('bundles/<int:pk>/delete/', views.bundle_delete, name='bundle_delete'),
    
    # Monitoring & Clients
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('licenses/', views.license_list, name='license_list'),
    path('installations/', views.installation_list, name='installation_list'),
]

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
    path('modules/<int:pk>/sales/', views.module_sales, name='module_sales'),
    
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

    path('transactions/', views.order_list, name='order_list'),
    path('transactions/<int:pk>/', views.order_detail, name='order_detail'),
    path('licenses/', views.license_list, name='license_list'),
    path('support-subscriptions/', views.support_subscription_search, name='support_subscription_search'),

    path('installations/', views.installation_list, name='installation_list'),
    path('logs/', views.logs_view, name='logs_view'),
    
    # Messages du formulaire de contact
    path('contact-messages/', views.contact_message_list, name='contact_message_list'),
    path('contact-messages/<int:pk>/toggle-read/', views.contact_message_toggle_read, name='contact_message_toggle_read'),

    # Modération des avis
    path('reviews/', views.reviews_list, name='reviews_list'),
    path('reviews/<int:pk>/approve/', views.review_approve, name='review_approve'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
]

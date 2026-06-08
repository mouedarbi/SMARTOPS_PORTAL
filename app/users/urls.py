"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Gestion du routage d'URL pour l'application users.
              Inscrit les routes pour le dashboard client.
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('delete-account/', views.delete_account_confirm, name='delete_account_confirm'),
]

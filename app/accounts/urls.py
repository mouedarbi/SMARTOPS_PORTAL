"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Gestion du routage d'URL pour l'application accounts.
              Inscrit les routes pour le dashboard client.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]

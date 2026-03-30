"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration globale des routes (URLs) pour le projet Marketplace SMARTOPS.
              Ce fichier contient les patterns d'URLs pour les applications.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
]

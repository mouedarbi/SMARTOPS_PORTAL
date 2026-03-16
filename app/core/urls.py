"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Définition des routes locales pour l'application 'core'.
"""

from django.urls import path
from .views import home_view

urlpatterns = [
    path('', home_view, name='home'),
]

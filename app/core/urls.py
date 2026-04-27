"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Définition des routes locales pour l'application 'core'.
              Refonte : Activation de la vue home_view.
"""

from django.urls import path
from .views import home_view

app_name = 'core'

urlpatterns = [
    path('', home_view, name='home'),
]

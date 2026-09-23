"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : content
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Gestion du routage d'URL pour le contenu.
"""

from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('cgv/', views.render, name='cgv', kwargs={'template_name': 'content/cgv.html'}),
    path('confidentialite/', views.render, name='confidentialite', kwargs={'template_name': 'content/confidentialite.html'}),
]

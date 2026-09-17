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
    # Route par défaut (Index des contenus)
    path('', views.render, name='index', kwargs={'template_name': 'content/home_page.html'}),
    path('cgv/', views.render, name='cgv', kwargs={'template_name': 'content/cgv.html'}),
    path('confidentialite/', views.render, name='confidentialite', kwargs={'template_name': 'content/confidentialite.html'}),
]

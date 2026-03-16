"""
Fichier : apps.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration de l'application 'core' responsable des pages publiques du marketplace.
"""

from django.apps import AppConfig

class CoreConfig(AppConfig):
    """
    Classe de configuration pour l'application Django 'core'.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

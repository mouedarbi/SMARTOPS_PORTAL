"""
Fichier : apps.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration de l'application catalog.
"""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Configuration de l'application catalog."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'

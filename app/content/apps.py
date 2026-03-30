"""
Fichier : apps.py
Projet : Marketplace SMARTOPS
Application : content
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration de l'application content.
"""

from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content'

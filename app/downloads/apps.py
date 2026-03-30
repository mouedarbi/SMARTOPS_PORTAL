"""
Fichier : apps.py
Projet : Marketplace SMARTOPS
Application : downloads
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration de l'application downloads.
"""

from django.apps import AppConfig


class DownloadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'downloads'

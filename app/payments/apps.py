"""
Fichier : apps.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration de l'application payments.
"""

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configuration de l'application payments."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    def ready(self):
        """Branche les signaux d'émission automatique des factures."""
        from . import signals  # noqa: F401  (émission automatique des factures)

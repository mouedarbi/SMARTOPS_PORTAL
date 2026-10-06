"""
Fichier : apps.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration de l'application des comptes clients.
"""

from django.apps import AppConfig

class UsersConfig(AppConfig):
    """Configuration de l'application users."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Gestion des Utilisateurs'

    def ready(self):
        """Branche la journalisation des événements de compte."""
        # Journalisation des événements de compte (connexion, mot de passe, inscription…)
        from . import audit  # noqa: F401

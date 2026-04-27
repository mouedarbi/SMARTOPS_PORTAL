"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Définition du modèle utilisateur personnalisé.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour le Marketplace SMARTOPS.
    """
    LANGUAGES = [
        ('fr', 'Français'),
        ('en', 'English'),
    ]
    
    language_preference = models.CharField(
        max_length=5,
        choices=LANGUAGES,
        default='fr',
        verbose_name="Langue préférée"
    )
    
    is_client = models.BooleanField(
        default=True,
        verbose_name="Est un client"
    )

    def __str__(self):
        return self.username

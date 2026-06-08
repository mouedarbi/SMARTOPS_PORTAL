"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 3.0
Description : Définition du modèle utilisateur personnalisé.
              Implémente le droit à l'effacement RGPD (Art. 17) via anonymisation :
              les données d'identification sont effacées, les commandes et licences
              sont conservées pour les obligations fiscales (Art. 17.3.b RGPD).
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


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

    # --- RGPD Art. 17 — Droit à l'effacement ---
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Compte supprimé (RGPD)"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de suppression"
    )

    def __str__(self):
        return self.username

    def anonymize(self):
        """
        Anonymise les données personnelles de l'utilisateur conformément au
        droit à l'effacement (Art. 17 RGPD). Les enregistrements Order et License
        sont intentionnellement conservés pour respecter les obligations fiscales
        (conservation légale 7 ans — Art. 17.3.b RGPD).
        """
        token = uuid.uuid4().hex[:12]
        self.username = f"deleted_{token}"
        self.email = f"deleted_{token}@supprime.invalid"
        self.first_name = ""
        self.last_name = ""
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = timezone.now()
        # Invalide le mot de passe pour bloquer toute reconnexion
        self.set_unusable_password()
        self.save()

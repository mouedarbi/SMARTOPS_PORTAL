"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.3
Description : Définition des modèles pour la gestion des licences SMARTOPS.
              Modèles Django standards pour administration personnalisée.
"""

from django.db import models
from django.conf import settings
import uuid

class License(models.Model):
    """
    Modèle représentant une licence accordée pour un module spécifique.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='licenses',
        verbose_name="Propriétaire"
    )
    module = models.ForeignKey(
        'catalog.Module',
        on_delete=models.CASCADE,
        verbose_name="Module associé"
    )
    license_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=True,
        verbose_name="Clé de licence"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_active = models.BooleanField(default=True, verbose_name="Licence active")
    activation_count = models.IntegerField(default=0, verbose_name="Nombre d'activations")
    max_activations = models.IntegerField(default=1, verbose_name="Activations autorisées")
    
    # Hardware Binding
    installation_uuid = models.UUIDField(
        null=True, 
        blank=True, 
        editable=True, 
        verbose_name="UUID d'Installation liée"
    )

    class Meta:
        verbose_name = "Licence"
        verbose_name_plural = "Licences"
        ordering = ['-created_at']

    def __str__(self):
        return f"Licence {self.module.name} - {self.user.username}"

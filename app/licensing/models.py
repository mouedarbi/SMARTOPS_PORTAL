"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Définition des modèles pour la gestion des licences SMARTOPS.
              Gère les clés de licence, leur validité et les associations aux clients.
"""

from django.db import models
from django.conf import settings
import uuid

class License(models.Model):
    """
    Modèle représentant une licence accordée pour un module spécifique.
    
    @param user: Propriétaire de la licence.
    @param module: Module auquel la licence donne accès.
    @param license_key: Clé unique de la licence (UUID).
    @param is_active: État de validité de la licence.
    @param activation_count: Nombre de fois où la licence a été utilisée pour activation.
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
        editable=False,
        verbose_name="Clé de licence"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_active = models.BooleanField(default=True, verbose_name="Licence active")
    activation_count = models.IntegerField(default=0, verbose_name="Nombre d'activations")
    max_activations = models.IntegerField(default=1, verbose_name="Activations autorisées")

    class Meta:
        verbose_name = "Licence"
        verbose_name_plural = "Licences"
        ordering = ['-created_at']

    def __str__(self):
        return f"Licence {self.module.name} - {self.user.username}"

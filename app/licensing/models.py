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

class Installation(models.Model):
    """
    Représente une instance physique de SMARTOPS installée chez un client.
    Permet le monitoring technique et le support.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='installations',
        null=True, # Optionnel au début (Core App seulement)
        blank=True,
        verbose_name="Propriétaire"
    )
    installation_uuid = models.UUIDField(unique=True, verbose_name="UUID d'Installation")
    company_name = models.CharField(max_length=255, blank=True, verbose_name="Nom de l'Entreprise")
    core_version = models.CharField(max_length=50, default="1.0.0", verbose_name="Version du Noyau")
    last_sync = models.DateTimeField(auto_now=True, verbose_name="Dernière Synchronisation")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'Enregistrement")

    class Meta:
        verbose_name = "Installation"
        verbose_name_plural = "Installations"
        ordering = ['-last_sync']

    def __str__(self):
        return f"Machine {str(self.installation_uuid)[:8]}... ({self.user.username})"

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
    
    # Hardware Binding lié à une machine enregistrée
    installation = models.ForeignKey(
        Installation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='licenses',
        verbose_name="Installation liée"
    )

    class Meta:
        verbose_name = "Licence"
        verbose_name_plural = "Licences"
        ordering = ['-created_at']

    def __str__(self):
        return f"Licence {self.module.name} - {self.user.username}"

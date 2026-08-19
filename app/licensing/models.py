"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.4
Description : Définition des modèles pour la gestion des licences SMARTOPS.
              Modèles Django standards pour administration personnalisée.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

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
        verbose_name=_("Propriétaire")
    )
    installation_uuid = models.UUIDField(unique=True, verbose_name=_("UUID d'Installation"))
    company_name = models.CharField(max_length=255, blank=True, verbose_name=_("Nom de l'Entreprise"))
    core_version = models.CharField(max_length=50, default="1.0.0", verbose_name=_("Version du Noyau"))
    last_sync = models.DateTimeField(auto_now=True, verbose_name=_("Dernière Synchronisation"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'Enregistrement"))

    class Meta:
        verbose_name = _("Installation")
        verbose_name_plural = _("Installations")
        ordering = ['-last_sync']

    def __str__(self):
        owner = self.user.username if self.user else "Non attribué"
        return f"Machine {str(self.installation_uuid)[:8]}... ({owner})"

class License(models.Model):
    """
    Modèle représentant une licence accordée pour un module spécifique.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='licenses',
        verbose_name=_("Propriétaire")
    )
    module = models.ForeignKey(
        'catalog.Module',
        on_delete=models.CASCADE,
        verbose_name=_("Module associé")
    )
    license_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=True,
        verbose_name=_("Clé de licence")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    is_active = models.BooleanField(default=True, verbose_name=_("Licence active"))
    activation_count = models.IntegerField(default=0, verbose_name=_("Nombre d'activations"))
    max_activations = models.IntegerField(default=1, verbose_name=_("Activations autorisées"))
    
    # Hardware Binding lié à une machine enregistrée
    installation = models.ForeignKey(
        Installation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='licenses',
        verbose_name=_("Installation liée")
    )

    class Meta:
        verbose_name = _("Licence")
        verbose_name_plural = _("Licences")
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(activation_count__lte=models.F("max_activations")),
                name="license_activation_count_lte_max_activations",
            )
        ]

    def __str__(self):
        return f"Licence {self.module.name} - {self.user.username}"

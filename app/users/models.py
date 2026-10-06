"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 3.2
Description : Définition du modèle utilisateur personnalisé.
              Implémente le droit à l'effacement RGPD (Art. 17) : le compte est d'abord
              désactivé (soft_delete), puis anonymisé après un délai de grâce : les données
              d'identification sont effacées, les commandes et licences sont conservées pour
              les obligations fiscales (Art. 17.3.b RGPD).
"""

import math
import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Domaine des adresses e-mail remplacées à l'anonymisation : un compte dont l'e-mail se termine
# par ce domaine est déjà anonymisé (convention partagée avec la commande anonymize_deleted_accounts).
ANONYMIZED_EMAIL_DOMAIN = '@supprime.invalid'


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour le Marketplace SMARTOPS.
    """
    LANGUAGES = [
        ('fr', _('Français')),
        ('en', _('English')),
        ('nl', _('Nederlands')),
    ]

    language_preference = models.CharField(
        max_length=5,
        choices=LANGUAGES,
        default='fr',
        verbose_name=_("Langue préférée")
    )

    is_client = models.BooleanField(
        default=True,
        verbose_name=_("Est un client")
    )

    # Choisi à l'inscription, jamais modifié ensuite : un particulier et une entreprise sont deux
    # comptes distincts (seul un compte professionnel a un profil de facturation et des factures).
    ACCOUNT_TYPES = [
        ('individual', _('Particulier')),
        ('professional', _('Professionnel')),
    ]
    account_type = models.CharField(
        max_length=12,
        choices=ACCOUNT_TYPES,
        default='individual',
        editable=False,
        verbose_name=_("Type de compte")
    )

    # --- RGPD Art. 17 — Droit à l'effacement ---
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Compte supprimé (RGPD)")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de suppression")
    )

    def __str__(self):
        return self.username

    @property
    def is_professional(self):
        """Vrai pour un compte professionnel."""
        return self.account_type == 'professional'

    @property
    def is_anonymized(self):
        """Vrai si le compte a été anonymisé."""
        return self.email.endswith(ANONYMIZED_EMAIL_DOMAIN)

    @property
    def days_until_anonymization(self):
        """Jours restants avant l'anonymisation d'un compte supprimé (0 : à la prochaine exécution de
        la commande planifiée). Calculé à partir de deleted_at et du réglage, jamais stocké.
        None si le compte n'est pas en attente d'anonymisation."""
        if not self.is_deleted or self.deleted_at is None or self.is_anonymized:
            return None
        due = self.deleted_at + timedelta(days=settings.ACCOUNT_ANONYMIZATION_DELAY_DAYS)
        return max(0, math.ceil((due - timezone.now()).total_seconds() / 86400))

    def soft_delete(self):
        """
        Suppression demandée par le client : le compte est désactivé (connexion impossible),
        sans toucher aux données personnelles ni au mot de passe. L'anonymisation définitive
        est faite par la commande planifiée anonymize_deleted_accounts, une fois le délai
        ACCOUNT_ANONYMIZATION_DELAY_DAYS écoulé depuis deleted_at.
        """
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'is_deleted', 'deleted_at'])

    def anonymize(self):
        """
        Anonymise les données personnelles de l'utilisateur conformément au
        droit à l'effacement (Art. 17 RGPD). Les enregistrements Order et License
        sont intentionnellement conservés pour respecter les obligations fiscales
        (conservation légale 7 ans — Art. 17.3.b RGPD).
        La date de la demande de suppression (deleted_at) est conservée si elle existe.
        """
        token = uuid.uuid4().hex[:12]
        self.username = f"deleted_{token}"
        self.email = f"deleted_{token}{ANONYMIZED_EMAIL_DOMAIN}"
        self.first_name = ""
        self.last_name = ""
        # Coordonnées d'entreprise : données personnelles pour un indépendant. Les factures émises
        # en gardent leur propre copie (conservation légale).
        BillingProfile.objects.filter(user=self).delete()
        # allauth garde sa propre copie de l'adresse e-mail (et des données des comptes sociaux).
        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import SocialAccount
        EmailAddress.objects.filter(user=self).delete()
        SocialAccount.objects.filter(user=self).delete()
        self.is_active = False
        self.is_deleted = True
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
        # Invalide le mot de passe pour bloquer toute reconnexion
        self.set_unusable_password()
        self.save()

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(is_deleted=True, deleted_at__isnull=True),
                name="user_deleted_at_required_if_deleted",
            )
        ]


class BillingProfile(models.Model):
    """Coordonnées de facturation d'un compte professionnel (entreprise établie en Belgique).

    Une facture en recopie le contenu au moment de l'achat : modifier ce profil ne change jamais
    une facture déjà émise.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='billing_profile',
        verbose_name=_("Client")
    )
    company_name = models.CharField(max_length=255, verbose_name=_("Raison sociale"))
    # Saisie libre, sans contrôle de format : un contrôle trop strict bloquait l'inscription.
    vat_number = models.CharField(max_length=30, verbose_name=_("Numéro de TVA"))
    street = models.CharField(max_length=255, verbose_name=_("Rue et numéro"))
    postal_code = models.CharField(max_length=10, verbose_name=_("Code postal"))
    city = models.CharField(max_length=100, verbose_name=_("Localité"))
    country = models.CharField(max_length=2, default='BE', editable=False, verbose_name=_("Pays"))

    class Meta:
        verbose_name = _("Profil de facturation")
        verbose_name_plural = _("Profils de facturation")

    def __str__(self):
        return f"{self.company_name} ({self.vat_number})"

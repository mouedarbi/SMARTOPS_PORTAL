"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.4
Description : Définition des modèles pour la gestion des transactions et paiements.
              Gestion du consentement légal de rétractation (Art. VI.53, 13° CDE)
              et contrainte de non-vacuité des commandes.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from catalog.models import Module, ModuleBundle

class Order(models.Model):
    """
    Modèle représentant une commande passée sur la Marketplace.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('completed', _('Terminée')),
        ('failed', _('Échouée')),
        ('refunded', _('Remboursée')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_("Client")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Statut")
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant total")
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("ID Paiement Stripe")
    )
    withdrawal_waiver_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consentement de renonciation au droit de rétractation (Art. VI.53, 13° CDE)")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Dernière modification"))

    def clean(self):
        super().clean()
        if self.status == 'completed' and self.pk and not self.items.exists():
            raise ValidationError({
                'status': _("Une commande ne peut être finalisée sans contenir au moins un élément (OrderItem).")
            })

    class Meta:
        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.id} - {self.user.username} ({self.status})"


class OrderItem(models.Model):
    """
    Modèle représentant un produit spécifique au sein d'une commande.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Commande")
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Module")
    )
    bundle = models.ForeignKey(
        ModuleBundle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Pack")
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Prix d'achat")
    )
    PRODUCT_TYPE_CHOICES = [
        ('module', _('Module')),
        ('support', _('Support annuel')),
    ]
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default='module',
        verbose_name=_("Type de produit")
    )

    class Meta:
        verbose_name = _("Élément de commande")
        verbose_name_plural = _("Éléments de commande")

    def __str__(self):
        item_name = self.module.name if self.module else (self.bundle.name if self.bundle else "Item")
        return f"{item_name} (Commande #{self.order.id})"

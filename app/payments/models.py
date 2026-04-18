"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.3
Description : Définition des modèles pour la gestion des transactions et paiements.
              Modèles Django standards pour administration personnalisée.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
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
        verbose_name="Client"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant total"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID Paiement Stripe"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
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
        verbose_name="Commande"
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Module"
    )
    bundle = models.ForeignKey(
        ModuleBundle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Pack"
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix d'achat"
    )

    class Meta:
        verbose_name = "Élément de commande"
        verbose_name_plural = "Éléments de commande"

    def __str__(self):
        item_name = self.module.name if self.module else self.bundle.name
        return f"{item_name} (Commande #{self.order.id})"

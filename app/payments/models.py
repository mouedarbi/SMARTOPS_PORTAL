"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Définition des modèles pour la gestion des transactions et paiements.
              Gère les commandes (Orders) et les éléments de commande (OrderItems)
              en lien avec le catalogue et les utilisateurs.
"""

from django.db import models
from django.conf import settings
from catalog.models import Module, ModuleBundle

class Order(models.Model):
    """
    Modèle représentant une commande passée sur la Marketplace.
    
    @param user: Référence vers l'utilisateur (client) ayant passé la commande.
    @param status: État actuel de la transaction (pending, completed, failed, refunded).
    @param total_amount: Montant total payé pour la commande.
    @param stripe_payment_intent_id: Identifiant technique de la transaction Stripe.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Terminée'),
        ('failed', 'Échouée'),
        ('refunded', 'Remboursée'),
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
    Un élément peut être soit un module individuel, soit un pack (bundle).
    
    @param order: Référence vers la commande parente.
    @param module: Référence optionnelle vers un module unique.
    @param bundle: Référence optionnelle vers un pack de modules.
    @param price_at_purchase: Prix de l'élément au moment de la validation.
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

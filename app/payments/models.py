"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.6
Description : Définition des modèles pour la gestion des transactions et paiements.
              Gestion du consentement légal de rétractation (Art. VI.53, 13° CDE)
              et contrainte de non-vacuité des commandes.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
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
        ('refund_pending', _('Remboursement à traiter')),
        ('refunded', _('Remboursée')),
    ]
    # Commandes payées : elles comptent dans les recettes, diminuées des remboursements traités.
    PAID_STATUSES = ('completed', 'refund_pending', 'refunded')

    # PROTECT : une commande est conservée (obligation comptable, Art. 17.3.b RGPD) ;
    # la suppression d'un compte client passe par User.anonymize().
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
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
    refund_due_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Remboursement dû (somme des lignes)"),
        help_text=_("Montant à rembourser manuellement via Stripe, somme des remboursements dus sur les "
                     "lignes de la commande. Conservé une fois le remboursement traité.")
    )
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Remboursement traité le")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Dernière modification"))

    def record_refunds(self, refunds):
        """Consigne des remboursements dus sur les lignes de cette commande.

        `refunds` : liste de triplets (ligne, montant, motif). Le total de la commande devient la
        somme des remboursements de toutes ses lignes, au lieu d'être écrasé à chaque ligne.
        """
        for item, amount, reason in refunds:
            item.refund_due_amount = amount
            item.refund_reason = reason
            item.save(update_fields=['refund_due_amount', 'refund_reason'])
        self.refund_due_amount = self.items.aggregate(total=models.Sum('refund_due_amount'))['total']
        self.status = 'refund_pending'
        self.save(update_fields=['refund_due_amount', 'status'])

    def mark_refunds_processed(self):
        """Remboursement traité : le montant et le motif de chaque ligne sont conservés, datés."""
        now = timezone.now()
        self.items.filter(refund_due_amount__isnull=False, refunded_at__isnull=True).update(refunded_at=now)
        self.refunded_at = now
        self.status = 'refunded'
        self.save(update_fields=['refunded_at', 'status'])

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
    # Remboursement consigné ligne par ligne à la suppression du compte : une même commande peut
    # porter plusieurs remboursements (support et licence). Order.refund_due_amount en est la somme.
    REFUND_REASON_CHOICES = [
        ('withdrawal_support', _('Support · rétractation')),
        ('unused_license', _('Licence jamais activée')),
        ('no_waiver', _('Licence sans renonciation à la rétractation')),
    ]
    refund_due_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Remboursement dû pour cette ligne")
    )
    refund_reason = models.CharField(
        max_length=20,
        choices=REFUND_REASON_CHOICES,
        blank=True,
        verbose_name=_("Motif du remboursement")
    )
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Remboursement traité le")
    )

    class Meta:
        verbose_name = _("Élément de commande")
        verbose_name_plural = _("Éléments de commande")

    def __str__(self):
        item_name = self.module.name if self.module else (self.bundle.name if self.bundle else "Item")
        return f"{item_name} (Commande #{self.order.id})"


class Invoice(models.Model):
    """Facture d'une commande passée par un compte professionnel.

    En Belgique, une facture est obligatoire pour un client professionnel (art. 53 §2 Code TVA),
    pas pour un particulier : seuls les comptes professionnels en reçoivent une, émise
    automatiquement au paiement. Toutes les mentions (vendeur, client, désignations, montants)
    sont recopiées à l'émission : la facture ne change plus si le profil, le catalogue ou le
    compte changent ensuite, et elle survit à l'anonymisation du compte (conservation 7 ans).
    Numérotation continue, sans trou (contrainte d'unicité sur `sequence`).
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='invoice',
        verbose_name=_("Commande")
    )
    sequence = models.PositiveIntegerField(unique=True, verbose_name=_("Numéro d'ordre"))
    number = models.CharField(max_length=20, unique=True, verbose_name=_("Numéro de facture"))
    issued_at = models.DateTimeField(verbose_name=_("Date de la facture"))
    seller = models.JSONField(verbose_name=_("Vendeur"))
    customer = models.JSONField(verbose_name=_("Client"))
    lines = models.JSONField(verbose_name=_("Lignes"))
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Taux de TVA (%)"))
    total_excl_vat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total hors TVA"))
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Montant de la TVA"))
    total_incl_vat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total TVA comprise"))

    class Meta:
        verbose_name = _("Facture")
        verbose_name_plural = _("Factures")
        ordering = ['-sequence']

    def __str__(self):
        return self.number

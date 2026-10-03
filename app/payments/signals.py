"""
Fichier : signals.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Émission automatique de la facture quand la commande d'un compte professionnel
              est payée, quel que soit le parcours (webhook Stripe, mode démo, données de test).
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order

audit_logger = logging.getLogger('audit')


@receiver(post_save, sender=Order)
def issue_invoice_when_paid(sender, instance, **kwargs):
    if instance.status != 'completed' or not instance.user.is_professional:
        return
    from .invoicing import issue_invoice
    try:
        issue_invoice(instance)
    except Exception:
        # Une facture manquante se rattrape (manage.py issue_missing_invoices) ; un paiement
        # enregistré ne doit jamais échouer à cause d'elle.
        audit_logger.exception(f"INVOICE FAILED: Order #{instance.pk} (user ID {instance.user_id}).")

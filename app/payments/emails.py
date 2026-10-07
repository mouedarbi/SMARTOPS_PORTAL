"""
Fichier : emails.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : E-mail de confirmation de commande envoyé par le Portal après un paiement
              (module, pack ou abonnement au support), dans la langue préférée du client.
              Facture PDF jointe pour un compte professionnel. Appelé explicitement par les
              vues de paiement, jamais par un signal : les scripts de données de démo
              n'envoient donc aucun e-mail.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation

from .models import Invoice

audit_logger = logging.getLogger('audit')


def send_order_confirmation(order, request):
    """Envoie le récapitulatif d'une commande payée à son client ; un échec est journalisé sans
    bloquer le paiement."""
    user = order.user
    if order.status != 'completed' or not user.email:
        return False
    language = user.language_preference if user.language_preference in dict(settings.LANGUAGES) else 'fr'
    try:
        with translation.override(language):
            invoice = Invoice.objects.filter(order=order).first() if user.is_professional else None
            context = {
                'user': user,
                'order': order,
                'items': order.items.select_related('module', 'bundle').order_by('pk'),
                'invoice': invoice,
                'dashboard_url': request.build_absolute_uri(reverse('users:dashboard')),
            }
            subject = settings.ACCOUNT_EMAIL_SUBJECT_PREFIX + ' '.join(
                render_to_string('payments/email/order_confirmation_subject.txt', context).split())
            message = EmailMultiAlternatives(
                subject=subject,
                body=render_to_string('payments/email/order_confirmation_message.txt', context),
                to=[user.email],
            )
            message.attach_alternative(render_to_string('payments/email/order_confirmation_message.html', context),
                                       'text/html')
            if invoice:
                from .invoicing import render_invoice_pdf
                message.attach(f"facture-{invoice.number}.pdf", render_invoice_pdf(invoice), 'application/pdf')
            message.send()
    except Exception:
        audit_logger.exception(f"ORDER CONFIRMATION EMAIL FAILED: Order #{order.pk} (user ID {user.pk}).")
        return False
    audit_logger.info(f"ORDER CONFIRMATION EMAIL SENT: Order #{order.pk} to user ID {user.pk} "
                      f"(language {language}, invoice {invoice.number if invoice else '-'}).")
    return True

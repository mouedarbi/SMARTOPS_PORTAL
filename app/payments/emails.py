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

from users.emails import send_customer_email

from .models import Invoice


def send_order_confirmation(order, request):
    """Envoie le récapitulatif d'une commande payée à son client ; un échec est journalisé sans
    bloquer le paiement."""
    user = order.user
    if order.status != 'completed':
        return False

    def build_context(request):
        invoice = Invoice.objects.filter(order=order).first() if user.is_professional else None
        context = {
            'order': order,
            'items': order.items.select_related('module', 'bundle').order_by('pk'),
            'invoice': invoice,
            # Art. VI.46 §7 CDE (art. 8 §7 b) directive 2011/83/UE) : la confirmation reprend
            # l'accord exprès du consommateur et la perte de son droit de rétractation. Seulement
            # pour un contenu numérique (module, pack), pas pour le support, qui est un service.
            'withdrawal_waiver_at': (order.withdrawal_waiver_accepted_at
                                     if not user.is_professional
                                     and order.items.exclude(product_type='support').exists() else None),
        }
        attachments = []
        if invoice:
            from .invoicing import render_invoice_pdf
            attachments.append((f"facture-{invoice.number}.pdf", render_invoice_pdf(invoice), 'application/pdf'))
        return context, attachments

    return send_customer_email(user, 'payments/email/order_confirmation', request, build_context,
                               log_label=f"Order #{order.pk}")

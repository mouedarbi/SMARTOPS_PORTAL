"""
Fichier : invoicing.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Émission et rendu PDF des factures des comptes professionnels.
              Mentions reprises de l'art. 53 §2 du Code TVA et de l'art. 5 de l'AR n° 1 :
              date, numéro séquentiel, vendeur (nom, adresse, n° d'entreprise, n° de TVA),
              client (nom, adresse, n° de TVA), désignation, base imposable, taux et montant
              de la TVA, total. Limite connue : entre deux assujettis belges, la facture
              électronique structurée (Peppol) est obligatoire depuis le 1er janvier 2026 ;
              le Portal produit un PDF, sans transmission Peppol.
"""

import io
import logging
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.formats import date_format, number_format
from django.utils import translation
from django.utils.translation import gettext as _

from .models import Invoice, Order

audit_logger = logging.getLogger('audit')

# Une facture est due pour une commande payée ; une commande remboursée ensuite garde la sienne.
INVOICEABLE_STATUSES = ('completed', 'refund_pending', 'refunded')
CENT = Decimal('0.01')


def _line_description(item):
    if item.bundle_id:
        return f"Pack {item.bundle.name}"
    name = item.module.name if item.module_id else "Module"
    if item.product_type == 'support':
        return f"Support annuel – {name}"
    return f"Licence – {name}"


def _split_vat(amount_incl, rate):
    """Prix TVA comprise -> (hors TVA, TVA), arrondis au cent ; leur somme vaut le prix payé."""
    excl = (amount_incl / (1 + rate / 100)).quantize(CENT)
    return excl, amount_incl - excl


def invoice_due(order):
    """Une facture n'est émise que pour une commande payée d'un compte professionnel."""
    return (order.status in INVOICEABLE_STATUSES and order.user.is_professional
            and order.items.exists() and not Invoice.objects.filter(order=order).exists())


def issue_invoice(order, issued_at=None):
    """Émet la facture d'une commande d'un compte professionnel ; None si elle n'est pas due.

    Le numéro suit le dernier numéro émis, dans la même transaction : la contrainte d'unicité
    empêche deux factures de partager un numéro, et aucun numéro n'est sauté.
    """
    from users.models import BillingProfile
    if not invoice_due(order):
        return None
    billing = BillingProfile.objects.filter(user=order.user).first()
    if billing is None:
        audit_logger.warning(f"INVOICE NOT ISSUED: Order #{order.pk} (professional user ID {order.user_id}) has no billing profile.")
        return None
    rate = Decimal(settings.INVOICE_VAT_RATE)
    lines = []
    for item in order.items.select_related('module', 'bundle').order_by('pk'):
        excl, vat = _split_vat(item.price_at_purchase, rate)
        lines.append({'description': _line_description(item), 'quantity': 1,
                      'total_excl_vat': str(excl), 'vat_amount': str(vat), 'total_incl_vat': str(item.price_at_purchase)})
    fields = {
        'order': order,
        'seller': dict(settings.INVOICE_SELLER),
        'customer': {'company_name': billing.company_name, 'vat_number': billing.vat_number,
                     'street': billing.street, 'postal_code': billing.postal_code,
                     'city': billing.city, 'country': billing.country},
        'lines': lines,
        'vat_rate': rate,
        'total_excl_vat': sum((Decimal(l['total_excl_vat']) for l in lines), Decimal('0')),
        'vat_amount': sum((Decimal(l['vat_amount']) for l in lines), Decimal('0')),
        'total_incl_vat': sum((Decimal(l['total_incl_vat']) for l in lines), Decimal('0')),
    }
    issued_at = issued_at or timezone.now()
    for _attempt in range(5):
        try:
            with transaction.atomic():
                last = Invoice.objects.select_for_update().order_by('-sequence').first()
                sequence = (last.sequence if last else 0) + 1
                invoice = Invoice.objects.create(sequence=sequence, number=f"F{issued_at:%Y}-{sequence:05d}",
                                                 issued_at=issued_at, **fields)
            break
        except IntegrityError:
            # Commande déjà facturée par une requête concurrente, ou numéro pris entre-temps : réessayer.
            existing = Invoice.objects.filter(order=order).first()
            if existing:
                return existing
    else:
        audit_logger.error(f"INVOICE NOT ISSUED: Order #{order.pk}, no free invoice number after 5 attempts.")
        return None
    audit_logger.info(f"INVOICE ISSUED: {invoice.number} for Order #{order.pk} (user ID {order.user_id}).")
    return invoice


def issue_missing_invoices():
    """Factures des commandes payées de comptes professionnels qui n'en ont pas encore, datées du
    jour de la commande, dans l'ordre chronologique des commandes."""
    orders = (Order.objects
              .filter(status__in=INVOICEABLE_STATUSES, user__account_type='professional', invoice__isnull=True)
              .select_related('user')
              .order_by('created_at', 'pk'))
    return [invoice for invoice in (issue_invoice(order, issued_at=order.created_at) for order in orders) if invoice]


def _money(value):
    return f"{number_format(Decimal(value), 2, force_grouping=True)} €"


def render_invoice_pdf(invoice):
    """PDF A4 de la facture, construit uniquement à partir des données recopiées à l'émission.

    Toujours en français, langue de l'original (vendeur établi à Bruxelles), quelle que soit la
    langue de l'interface.
    """
    with translation.override('fr'):
        return _render_invoice_pdf(invoice)


def _render_invoice_pdf(invoice):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    seller, customer = invoice.seller, invoice.customer
    styles = getSampleStyleSheet()
    small = styles['Normal'].clone('small', fontSize=8, leading=10, textColor=colors.grey)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=f"{_('Facture')} {invoice.number}", author=seller['name'])

    def address(party, name_key):
        return '<br/>'.join([f"<b>{party[name_key]}</b>", party['street'],
                             f"{party['postal_code']} {party['city']}", _("Belgique")])

    parties = Table([[
        Paragraph(address(seller, 'name') + '<br/>' + _("N° d'entreprise : %(number)s") % {'number': seller['company_number']}
                  + '<br/>' + _("TVA : %(vat)s") % {'vat': seller['vat_number']}, styles['Normal']),
        Paragraph(f"<b>{_('Facturé à')}</b><br/>" + address(customer, 'company_name')
                  + '<br/>' + _("TVA : %(vat)s") % {'vat': customer['vat_number']}, styles['Normal']),
    ]], colWidths=[87 * mm, 87 * mm])
    parties.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

    header = [_("Désignation"), _("Qté"), _("Hors TVA"), _("TVA %(rate)s %%") % {'rate': number_format(invoice.vat_rate, 0)},
              _("TVA comprise")]
    rows = [header] + [[Paragraph(l['description'], styles['Normal']), str(l['quantity']), _money(l['total_excl_vat']),
                        _money(l['vat_amount']), _money(l['total_incl_vat'])] for l in invoice.lines]
    rows += [['', '', _money(invoice.total_excl_vat), _money(invoice.vat_amount), _money(invoice.total_incl_vat)]]
    lines = Table(rows, colWidths=[78 * mm, 12 * mm, 28 * mm, 28 * mm, 28 * mm], repeatRows=1)
    lines.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 0.8, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F1F5F9')]),
    ]))

    story = [
        Paragraph(f"{_('Facture')} {invoice.number}", styles['Title']),
        Paragraph(_("Date de la facture : %(date)s") % {'date': date_format(timezone.localtime(invoice.issued_at), 'DATE_FORMAT')}
                  + '<br/>' + _("Commande n° %(id)s, payée par carte bancaire (Stripe).") % {'id': invoice.order_id},
                  styles['Normal']),
        Spacer(1, 8 * mm), parties, Spacer(1, 10 * mm), lines, Spacer(1, 6 * mm),
        Paragraph(_("Montant total payé : %(total)s, TVA belge de %(rate)s %% comprise. Facture acquittée.")
                  % {'total': _money(invoice.total_incl_vat), 'rate': number_format(invoice.vat_rate, 0)}, styles['Normal']),
    ]
    if settings.INVOICE_SELLER_FICTITIOUS:
        story += [Spacer(1, 10 * mm), Paragraph(
            _("Document de démonstration (projet de fin d'études) : les coordonnées du vendeur sont fictives."), small)]
    doc.build(story)
    return buffer.getvalue()

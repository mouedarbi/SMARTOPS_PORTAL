"""
Fichier : price_tags.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Affichage des prix selon le type de compte : TTC pour un particulier ou un visiteur,
              HTVA puis TTC en dessous pour un professionnel. Les prix sont stockés TVA comprise.
"""

from decimal import Decimal

from django import template
from django.conf import settings

from payments.invoicing import split_vat

register = template.Library()


def _viewer(context, user):
    """Utilisateur pour qui le prix est affiché : celui passé au tag, sinon celui de la requête."""
    if user is not None:
        return user
    request = context.get('request')
    return getattr(request, 'user', None) or context.get('user')


@register.inclusion_tag('core/_price.html', takes_context=True)
def price(context, amount, decimals=2, secondary=True, inline=False, user=None, excl=None):
    """
    Prix TVA comprise `amount` : « 149,00 € TTC » pour un particulier ou un visiteur ;
    « 123,14 € HTVA » puis « 149,00 € TTC » pour un professionnel (même arrondi que la facture).
    secondary=False n'affiche que la première ligne (prix barré) ; inline=True tient sur une ligne (bouton, liste).
    excl : montant hors TVA déjà calculé (total d'une facture, somme de ses lignes arrondies une à une).
    """
    incl = Decimal(str(amount if amount is not None else 0))
    viewer = _viewer(context, user)
    professional = bool(getattr(viewer, 'is_authenticated', False) and getattr(viewer, 'is_professional', False))
    if excl is None:
        excl, _vat = split_vat(incl, Decimal(settings.INVOICE_VAT_RATE))
    return {'incl': incl, 'excl': excl, 'professional': professional,
            'decimals': decimals, 'secondary': secondary, 'inline': inline}

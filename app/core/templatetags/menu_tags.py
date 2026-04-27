"""
Fichier : menu_tags.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Template tags pour récupérer et afficher les menus (Version Simple).
"""

from django import template
from core.models import Menu

register = template.Library()

@register.simple_tag
def get_menu(slug):
    """
    Récupère un menu par son slug.
    """
    try:
        return Menu.objects.filter(slug=slug).first()
    except Exception:
        return None

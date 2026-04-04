"""
Fichier : menu_tags.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Template tags pour récupérer et afficher les menus traduisibles.
"""

from django import template
from core.models import Menu
from wagtail.models import Locale

register = template.Library()

@register.simple_tag(takes_context=True)
def get_menu(context, slug):
    """
    Récupère un menu par son slug et sa langue (locale).
    @param slug : Le slug du menu (ex: 'main-menu')
    @return : L'objet Menu correspondant à la langue courante.
    """
    request = context.get('request')
    if not request:
        return None
        
    # On récupère la locale courante du thread (Wagtail i18n)
    try:
        active_locale = Locale.get_active()
    except:
        # Fallback sur la locale par défaut si Wagtail n'est pas encore prêt
        active_locale = Locale.get_default()
    
    try:
        # On cherche le menu qui a le slug ET la bonne locale
        return Menu.objects.filter(slug=slug, locale=active_locale).first()
    except Exception:
        # En cas d'erreur DB (ex: table non créée lors du premier lancement)
        return None

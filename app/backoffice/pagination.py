"""
Fichier : pagination.py
Projet : Marketplace SMARTOPS
Application : backoffice
Description : Pagination commune aux écrans de liste du backoffice, avec choix de la taille de page.
"""

from django.core.paginator import Paginator

PER_PAGE_CHOICES = (10, 50, 100)
DEFAULT_PER_PAGE = 10
SESSION_KEY = 'backoffice_per_page'


def get_per_page(request):
    """
    Taille de page demandée (?per_page=10|50|100). Une valeur valide est mémorisée en session
    pour tous les écrans ; une valeur absente ou invalide retombe sur la dernière taille choisie,
    puis sur la valeur par défaut.
    """
    try:
        requested = int(request.GET.get('per_page', ''))
    except (TypeError, ValueError):
        requested = None
    if requested in PER_PAGE_CHOICES:
        request.session[SESSION_KEY] = requested
        return requested
    remembered = request.session.get(SESSION_KEY)
    return remembered if remembered in PER_PAGE_CHOICES else DEFAULT_PER_PAGE


def paginate(request, items):
    """Retourne la page courante de `items` (queryset ou liste) ; la page reste valide même si ?page= est absurde."""
    page = Paginator(items, get_per_page(request)).get_page(request.GET.get('page'))
    page.per_page_choices = PER_PAGE_CHOICES  # utilisé par _pagination.html
    return page

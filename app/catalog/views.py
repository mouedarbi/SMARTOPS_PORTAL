"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Vues pour le catalogue de modules.
"""

from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from wagtail.models import Locale
from .models import Module, Category

def module_list(request):
    """
    Affiche la liste complète des modules du catalogue.
    Possibilité de filtrer par catégorie via ?category=slug
    Filtrage par langue active pour éviter les doublons de traduction.
    """
    current_language = get_language()
    current_locale = Locale.objects.get(language_code=current_language)
    
    category_slug = request.GET.get('category')
    
    # Filtrer par la langue courante
    modules = Module.objects.filter(is_active=True, locale=current_locale).order_by('-created_at')
    categories = Category.objects.filter(locale=current_locale)

    if category_slug:
        modules = modules.filter(category__slug=category_slug)

    context = {
        'modules': modules,
        'categories': categories,
        'selected_category': category_slug,
    }
    return render(request, 'catalog/module_list.html', context)

def module_detail(request, slug):
    """
    Affiche les détails d'un module spécifique.
    """
    module = get_object_or_404(Module, slug=slug, is_active=True)
    context = {
        'module': module,
    }
    return render(request, 'catalog/module_detail.html', context)

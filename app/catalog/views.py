"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Vues pour le catalogue de modules.
"""

from django.shortcuts import render, get_object_or_404
from .models import Module, Category

def module_list(request):
    """
    Affiche la liste complète des modules du catalogue.
    Possibilité de filtrer par catégorie via ?category=slug
    """
    category_slug = request.GET.get('category')
    modules = Module.objects.filter(is_active=True).order_by('-created_at')
    categories = Category.objects.all()

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

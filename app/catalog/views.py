"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Vues pour le catalogue de modules (Version sans Wagtail).
"""

from django.conf import settings
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Module, Category, ModuleBundle, Review
from licensing.models import License
from payments.models import OrderItem

def _slug_query(field_path, slug):
    """
    Construit une requête OR sur les colonnes de slug traduites (slug_fr, slug_en, slug_nl...).
    modeltranslation ne fait pas de repli automatique sur les lookups .filter() : un slug généré
    dans une langue ne matcherait donc plus après un changement de langue sans cette requête.
    """
    query = Q()
    for lang_code, _ in settings.LANGUAGES:
        query |= Q(**{f"{field_path}_{lang_code}": slug})
    return query

def module_list(request):
    """
    Affiche la liste complète des modules du catalogue.
    Possibilité de filtrer par catégorie via ?category=slug
    """
    category_slug = request.GET.get('category')

    modules = Module.objects.filter(is_active=True).order_by('-created_at')
    categories = Category.objects.all()

    if category_slug:
        modules = modules.filter(_slug_query('category__slug', category_slug))

    context = {
        'modules': modules,
        'categories': categories,
        'selected_category': category_slug,
    }
    return render(request, 'catalog/module_list.html', context)

def module_detail(request, slug):
    """
    Affiche les détails d'un module spécifique et gère la soumission des avis.
    """
    module = get_object_or_404(Module.objects.filter(_slug_query('slug', slug), is_active=True))
    # Affichage uniquement des avis approuvés par l'admin
    reviews = module.reviews.filter(is_approved=True).select_related('user')
    
    can_review = False
    has_reviewed = False
    
    if request.user.is_authenticated:
        can_review = License.objects.filter(user=request.user, module=module, is_active=True).exists()
        has_reviewed = module.reviews.filter(user=request.user).exists()
        
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour poster un avis.")
            return redirect('catalog:module_detail', slug=slug)
            
        if not can_review:
            messages.error(request, "Seuls les utilisateurs possédant une licence active pour ce module peuvent l'évaluer.")
            return redirect('catalog:module_detail', slug=slug)
            
        if has_reviewed:
            messages.error(request, "Vous avez déjà soumis un avis pour ce module.")
            return redirect('catalog:module_detail', slug=slug)
            
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or not comment:
            messages.error(request, "Veuillez fournir une note et un commentaire.")
            return redirect('catalog:module_detail', slug=slug)
            
        # Création de l'avis en attente de modération (pas de traduction immédiate)
        Review.objects.create(
            user=request.user,
            module=module,
            rating=int(rating),
            comment=comment,
            comment_language=getattr(request, 'LANGUAGE_CODE', 'fr'),
            is_approved=False
        )
        messages.success(request, "Votre avis a été soumis avec succès et sera publié après validation par un administrateur.")
        return redirect('catalog:module_detail', slug=slug)

    # Calcul de la moyenne des notes
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    context = {
        'module': module,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'can_review': can_review and not has_reviewed,
        'has_reviewed': has_reviewed,
    }
    return render(request, 'catalog/module_detail.html', context)

def bundle_detail(request, slug):
    """
    Affiche les détails d'un pack de modules spécifique et gère la soumission des avis.
    """
    bundle = get_object_or_404(ModuleBundle.objects.filter(_slug_query('slug', slug), is_active=True))
    # Affichage uniquement des avis approuvés par l'admin
    reviews = bundle.reviews.filter(is_approved=True).select_related('user')
    
    can_review = False
    has_reviewed = False
    
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user, 
            order__status='completed', 
            bundle=bundle
        ).exists()
        has_reviewed = bundle.reviews.filter(user=request.user).exists()
        
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour poster un avis.")
            return redirect('catalog:bundle_detail', slug=slug)
            
        if not can_review:
            messages.error(request, "Seuls les utilisateurs ayant acheté ce pack peuvent l'évaluer.")
            return redirect('catalog:bundle_detail', slug=slug)
            
        if has_reviewed:
            messages.error(request, "Vous avez déjà soumis un avis pour ce pack.")
            return redirect('catalog:bundle_detail', slug=slug)
            
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or not comment:
            messages.error(request, "Veuillez fournir une note et un commentaire.")
            return redirect('catalog:bundle_detail', slug=slug)
            
        # Création de l'avis en attente de modération (pas de traduction immédiate)
        Review.objects.create(
            user=request.user,
            bundle=bundle,
            rating=int(rating),
            comment=comment,
            comment_language=getattr(request, 'LANGUAGE_CODE', 'fr'),
            is_approved=False
        )
        messages.success(request, "Votre avis a été soumis avec succès et sera publié après validation par un administrateur.")
        return redirect('catalog:bundle_detail', slug=slug)

    # Calcul de la moyenne des notes
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    context = {
        'bundle': bundle,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'can_review': can_review and not has_reviewed,
        'has_reviewed': has_reviewed,
    }
    return render(request, 'catalog/bundle_detail.html', context)

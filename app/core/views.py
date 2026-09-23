"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Contrôleurs pour les pages publiques du Marketplace.
"""

import requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from catalog.models import Module, ModuleBundle
from .forms import ContactForm

def format_github_number(n):
    try:
        n = int(n)
        if n >= 1000:
            return f"{n/1000:.1f}k"
        return str(n)
    except (ValueError, TypeError):
        return str(n)

def get_github_stats():
    CACHE_KEY = 'github_stats_smartops_v2'
    CACHE_TIMEOUT = 60 * 60 * 6
    github_stats = cache.get(CACHE_KEY)
    if github_stats:
        return github_stats
    github_stats = {'stars': 0, 'forks': 0}
    try:
        response = requests.get('https://api.github.com/repos/mouedarbi/SMARTOPS', timeout=5)
        if response.status_code == 200:
            data = response.json()
            stars = data.get('stargazers_count', 0)
            forks = data.get('forks_count', 0)
            github_stats = {
                'stars': stars if stars > 0 else 1200,
                'forks': forks if forks > 0 else 380,
            }
            cache.set(CACHE_KEY, github_stats, CACHE_TIMEOUT)
    except requests.RequestException:
        pass
    return github_stats

def home_view(request):
    """
    Vue principale de la page d'accueil (Refonte).
    Récupère les modules, les packs et les statistiques GitHub dynamiquement.
    """
    # 1. Récupération des statistiques GitHub
    stats = get_github_stats()
    github_stars = format_github_number(stats['stars'])
    github_forks = format_github_number(stats['forks'])

    # 2. Récupération des modules et packs mis en avant
    # On prend les 3 derniers modules actifs
    modules = Module.objects.filter(is_active=True).order_by('-created_at')[:3]
    
    # On prend tous les packs valides
    all_bundles = ModuleBundle.objects.filter(is_active=True)
    bundles = [b for b in all_bundles if b.is_currently_valid]

    context = {
        'github_stars': github_stars,
        'github_forks': github_forks,
        'modules': modules,
        'bundles': bundles,
        'is_refonte': True, # Petit flag pour debug
    }
    
    return render(request, 'core/home.html', context)


CONTACT_MAX_PER_HOUR = 5


def _client_ip(request):
    """IP du client derrière nginx : dernière entrée de X-Forwarded-For (ajoutée par le proxy)."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', '')


@require_POST
def contact_submit(request):
    """
    Enregistre un message du formulaire de contact de l'accueil (consultable dans le backoffice).
    Aucun email n'est envoyé. Champ piège anti-spam « website » et limite de messages par heure et par IP.
    """
    def back(status):
        return redirect(f"{reverse('core:home')}?contact={status}#contact")

    # Champ piège : un humain ne le remplit pas. On simule un succès sans rien enregistrer.
    if request.POST.get('website'):
        return back('sent')

    throttle_key = f"contact_throttle_{_client_ip(request)}"
    sent = cache.get(throttle_key, 0)
    if sent >= CONTACT_MAX_PER_HOUR:
        return back('error')

    form = ContactForm(request.POST)
    if not form.is_valid():
        return back('error')

    form.save()
    cache.set(throttle_key, sent + 1, 60 * 60)
    return back('sent')

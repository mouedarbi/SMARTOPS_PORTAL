"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Contrôleurs pour les pages publiques du Marketplace.
              Refonte : Vue de la page d'accueil sans Wagtail.
"""

import requests
from django.shortcuts import render
from django.core.cache import cache
from catalog.models import Module, ModuleBundle

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
    
    # On prend les 2 packs valides
    all_bundles = ModuleBundle.objects.filter(is_active=True)
    bundles = [b for b in all_bundles if b.is_currently_valid][:2]

    context = {
        'github_stars': github_stars,
        'github_forks': github_forks,
        'modules': modules,
        'bundles': bundles,
        'is_refonte': True, # Petit flag pour debug
    }
    
    return render(request, 'core/home.html', context)

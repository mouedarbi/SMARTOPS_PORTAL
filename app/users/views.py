"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Définition des vues pour la gestion des comptes clients.
              Inclut le tableau de bord (Dashboard) affichant les licences et commandes.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from payments.models import Order
from licensing.models import License

@login_required
def dashboard(request):
    """
    Affiche le tableau de bord de l'utilisateur connecté.
    Récupère les licences actives et l'historique des commandes.
    
    @param request: Objet HttpRequest de Django.
    @return: Rendu du template account/dashboard.html avec le contexte utilisateur.
    """
    user_licenses = License.objects.filter(user=request.user, is_active=True).select_related('module')
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'licenses': user_licenses,
        'orders': user_orders,
        'title': "Mon Tableau de Bord"
    }
    
    return render(request, 'account/dashboard.html', context)

@login_required
def profile(request):
    """
    Affiche le profil de l'utilisateur.
    """
    context = {
        'title': "Mon Profil"
    }
    return render(request, 'account/profile.html', context)

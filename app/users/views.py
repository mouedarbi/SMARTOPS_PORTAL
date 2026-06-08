"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Vues pour la gestion des comptes clients.
              Inclut le droit à l'effacement RGPD (Art. 17) via la vue
              delete_account_confirm qui anonymise les données personnelles
              tout en conservant l'historique des commandes (obligation fiscale).
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from payments.models import Order
from licensing.models import License


@login_required
def dashboard(request):
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
    context = {'title': "Mon Profil"}
    return render(request, 'account/profile.html', context)


@login_required
def delete_account_confirm(request):
    """
    Affiche la page de confirmation de suppression de compte (GET)
    et exécute l'anonymisation RGPD (POST).

    Conformément à l'Art. 17 RGPD, les données d'identification sont effacées.
    Les commandes et licences sont conservées (obligation fiscale Art. 17.3.b).
    """
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation', '')
        if confirmation == 'SUPPRIMER':
            user = request.user
            logout(request)
            user.anonymize()
            messages.success(
                request,
                _("Votre compte a été supprimé. Vos données personnelles ont été effacées conformément au RGPD.")
            )
            return redirect('core:home')
        else:
            messages.error(request, _("Confirmation incorrecte. Veuillez saisir SUPPRIMER pour confirmer."))
            return redirect('users:delete_account_confirm')

    return render(request, 'account/delete_account_confirm.html', {'title': _("Supprimer mon compte")})

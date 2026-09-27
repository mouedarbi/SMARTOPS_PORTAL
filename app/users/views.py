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
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from payments.models import Order
from licensing.models import License, SupportSubscription


@login_required
def dashboard(request):
    # Récupérer toutes les licences actives de l'utilisateur
    licenses_queryset = License.objects.filter(user=request.user, is_active=True).select_related('module')
    
    # Regrouper les licences par module
    grouped_licenses = {}
    for lic in licenses_queryset:
        mod_id = lic.module.id
        if mod_id not in grouped_licenses:
            grouped_licenses[mod_id] = {
                'module': lic.module,
                'total_max_activations': 0,
                'total_activation_count': 0,
                'unused_keys': [],
            }
        
        grouped_licenses[mod_id]['total_max_activations'] += lic.max_activations
        grouped_licenses[mod_id]['total_activation_count'] += lic.activation_count
        
        # Une clé est considérée comme inutilisée s'il n'y a pas d'installation liée
        if not lic.installation:
            grouped_licenses[mod_id]['unused_keys'].append({
                'id': lic.id,
                'key': str(lic.license_key)
            })
            
    # Statut de l'abonnement support, par module, en une seule requête
    subs_by_module = {
        sub.module_id: sub
        for sub in SupportSubscription.objects.filter(user=request.user, module_id__in=grouped_licenses.keys())
    }
    for mod_id, data in grouped_licenses.items():
        sub = subs_by_module.get(mod_id)
        data['support_active'] = bool(sub and sub.is_valid)
        data['support_expires_at'] = sub.expires_at if sub else None

    # Convertir en liste de dictionnaires pour le template
    licenses_list = list(grouped_licenses.values())
    
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    context = {
        'licenses': licenses_list,
        'orders': user_orders,
        'title': "Mon Tableau de Bord"
    }
    return render(request, 'account/dashboard.html', context)


@login_required
def profile(request):
    context = {'title': "Mon Profil"}
    return render(request, 'account/profile.html', context)


def account_holdings(user):
    """Produits et services du client au moment de sa demande de suppression.

    Une entrée par licence active (avec la fin de son support annuel s'il est encore valide),
    plus les supports encore valides sur un module sans licence active.
    """
    supports = {
        sub.module_id: sub
        for sub in SupportSubscription.objects.filter(user=user, expires_at__gt=timezone.now()).select_related('module')
    }
    holdings = []
    for lic in License.objects.filter(user=user, is_active=True).select_related('module').order_by('module__name'):
        support = supports.pop(lic.module_id, None)
        holdings.append({
            'module': lic.module,
            'license_key': lic.license_key,
            'support_until': support.expires_at if support else None,
        })
    for support in supports.values():
        holdings.append({'module': support.module, 'license_key': None, 'support_until': support.expires_at})
    return holdings


@login_required
def delete_account_confirm(request):
    """
    Affiche la page de confirmation de suppression de compte (GET)
    et exécute l'anonymisation RGPD (POST).

    Conformément à l'Art. 17 RGPD, les données d'identification sont effacées.
    Les commandes et licences sont conservées (obligation fiscale Art. 17.3.b).
    La suppression n'est jamais refusée : si le client possède des produits ou un support,
    la page les liste et il doit confirmer y renoncer, sans remboursement.
    """
    holdings = account_holdings(request.user)
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation', '')
        if confirmation != 'SUPPRIMER':
            messages.error(request, _("Confirmation incorrecte. Veuillez saisir SUPPRIMER pour confirmer."))
            return redirect('users:delete_account_confirm')
        if holdings and not request.POST.get('accept_no_refund'):
            messages.error(request, _("Veuillez confirmer que vous renoncez à vos produits et services, sans remboursement."))
            return redirect('users:delete_account_confirm')
        user = request.user
        logout(request)
        user.anonymize()
        messages.success(
            request,
            _("Votre compte a été supprimé. Vos données personnelles ont été effacées conformément au RGPD.")
        )
        return redirect('core:home')

    return render(request, 'account/delete_account_confirm.html', {
        'title': _("Supprimer mon compte"),
        'holdings': holdings,
    })

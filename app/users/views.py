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

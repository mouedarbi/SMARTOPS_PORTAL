"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Vues pour la gestion des comptes clients.
              Inclut le droit à l'effacement RGPD (Art. 17) via la vue
              delete_account_confirm qui désactive le compte ; ses données personnelles
              sont anonymisées après un délai de grâce, l'historique des commandes étant
              conservé (obligation fiscale).
"""

from django.conf import settings
from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.utils.formats import number_format
from django.utils.translation import gettext_lazy as _
import logging
from datetime import timedelta
from decimal import Decimal
from payments.models import Invoice, Order
from licensing.models import License, SupportSubscription
from .forms import BillingProfileForm
from .models import BillingProfile

audit_logger = logging.getLogger('audit')


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
    
    user_orders = Order.objects.filter(user=request.user).select_related('invoice').order_by('-created_at')[:5]
    context = {
        'licenses': licenses_list,
        'orders': user_orders,
        'invoices': Invoice.objects.filter(order__user=request.user) if request.user.is_professional else None,
        'title': "Mon Tableau de Bord"
    }
    return render(request, 'account/dashboard.html', context)


@login_required
def profile(request):
    context = {
        'title': "Mon Profil",
        'billing_profile': BillingProfile.objects.filter(user=request.user).first(),
    }
    return render(request, 'account/profile.html', context)


@login_required
def billing_profile_edit(request):
    """Modification des coordonnées de facturation, réservée aux comptes professionnels.

    Le type de compte, lui, ne se modifie jamais. Les factures déjà émises gardent leur copie.
    """
    if not request.user.is_professional:
        raise Http404
    billing = BillingProfile.objects.filter(user=request.user).first()
    form = BillingProfileForm(request.POST or None, instance=billing)
    if request.method == 'POST' and form.is_valid():
        billing = form.save(commit=False)
        billing.user = request.user
        billing.save()
        audit_logger.info(f"BILLING PROFILE UPDATE: User {request.user.username} (ID: {request.user.pk}).")
        messages.success(request, _("Vos coordonnées de facturation ont été enregistrées."))
        return redirect('users:profile')
    return render(request, 'account/billing_profile_form.html', {'form': form, 'title': _("Coordonnées de facturation")})


WITHDRAWAL_PERIOD_DAYS = 14


def _support_refund_due(user, module):
    """Montant dû si le client exerce son droit de rétractation sur ce support.

    Un abonnement de support est un service, pas un contenu numérique : il ne peut jamais être
    « entièrement exécuté » dans le délai légal de 14 jours (Art. VI.47 et VI.51 CDE, art. 14§3
    directive 2011/83/UE), contrairement aux modules. Dans ce délai, la rétractation ouvre donc
    droit au remboursement du prix payé, moins la part déjà consommée au prorata des jours
    écoulés. Passé ce délai, rien n'est dû : ni case à cocher ni CGV ne peuvent créer ou écarter
    cette obligation, elle découle directement de la loi.
    """
    from payments.models import OrderItem
    if user.is_professional:
        return None  # le droit de rétractation est réservé aux consommateurs
    item = (OrderItem.objects
            .filter(order__user=user, order__status='completed', product_type='support', module=module)
            .select_related('order')
            .order_by('-order__created_at')
            .first())
    if not item:
        return None
    elapsed = timezone.now() - item.order.created_at
    if elapsed >= timedelta(days=WITHDRAWAL_PERIOD_DAYS):
        return None
    consumed_fraction = min(Decimal(elapsed.days) / Decimal(365), Decimal('1'))
    amount = (item.price_at_purchase * (Decimal('1') - consumed_fraction)).quantize(Decimal('0.01'))
    return {
        'order': item.order,
        'item': item,
        'amount': amount,
        'deadline': item.order.created_at + timedelta(days=WITHDRAWAL_PERIOD_DAYS),
        'reason': 'withdrawal_support',
    }


def _license_from_order(user, module, order):
    """Licence de ce module délivrée au client par cette commande.

    Une licence ne référence pas la commande qui l'a créée. L'achat crée d'abord la commande,
    puis la licence : c'est donc la première licence de ce module créée pour ce client à partir
    de la date de la commande.
    """
    return (License.objects
            .filter(user=user, module=module, created_at__gte=order.created_at)
            .order_by('created_at')
            .first())


def _license_activated(lic):
    """Une licence a servi dès qu'elle a été liée à une installation ou activée au moins une fois."""
    return lic.installation_id is not None or lic.activation_count > 0


def _license_refund_due(user, order_item):
    """Montant dû pour une ligne de commande de module ou de pack, à la suppression du compte.

    Dans les 14 jours suivant la commande uniquement :
    - licence jamais activée : prix payé remboursé en entier (geste commercial) ;
    - licence activée sans renonciation enregistrée (anciennes commandes) : le droit de
      rétractation s'applique, prix payé remboursé en entier ;
    - licence activée avec renonciation (Art. VI.53, 13° CDE) : rien n'est dû.
    Un pack n'est remboursé, au prix du pack, que si aucune de ses licences n'a été activée
    (ou, sans renonciation, au titre du droit de rétractation). Passé 14 jours, rien n'est dû.
    Un défaut de conformité relève de la garantie légale et se traite au cas par cas.
    Compte professionnel : jamais de remboursement automatique (pas de droit de rétractation,
    réservé aux consommateurs, et pas de geste commercial).
    """
    order = order_item.order
    if user.is_professional:
        # Pas de droit de rétractation pour un professionnel, ni de geste commercial (choix du vendeur).
        return None
    if order.status != 'completed' or order_item.product_type != 'module':
        return None
    if timezone.now() - order.created_at >= timedelta(days=WITHDRAWAL_PERIOD_DAYS):
        return None
    if order_item.bundle_id:
        modules = list(order_item.bundle.modules.all())
    elif order_item.module_id:
        modules = [order_item.module]
    else:
        return None
    licenses = [_license_from_order(user, module, order) for module in modules]
    if not licenses or any(lic is None or not lic.is_active for lic in licenses):
        return None
    if not any(_license_activated(lic) for lic in licenses):
        reason = 'unused_license'
    elif order.withdrawal_waiver_accepted_at is None:
        reason = 'no_waiver'
    else:
        return None
    return {
        'order': order,
        'item': order_item,
        'amount': order_item.price_at_purchase,
        'deadline': order.created_at + timedelta(days=WITHDRAWAL_PERIOD_DAYS),
        'reason': reason,
        'licenses': licenses,
    }


def _license_refunds(user):
    """Remboursements de licences dus au client, indexés par identifiant de licence.

    Une licence n'est jamais rattachée à deux remboursements.
    """
    from payments.models import OrderItem
    since = timezone.now() - timedelta(days=WITHDRAWAL_PERIOD_DAYS)
    items = (OrderItem.objects
             .filter(order__user=user, order__status='completed', product_type='module', order__created_at__gt=since)
             .select_related('order', 'module', 'bundle')
             .order_by('order__created_at', 'pk'))
    by_license = {}
    for item in items:
        refund = _license_refund_due(user, item)
        if refund and not any(lic.pk in by_license for lic in refund['licenses']):
            for lic in refund['licenses']:
                by_license[lic.pk] = refund
    return by_license


def account_holdings(user):
    """Produits et services du client au moment de sa demande de suppression.

    Une entrée par licence active (avec la fin de son support annuel s'il est encore valide et
    le remboursement éventuellement dû pour la licence), plus les supports encore valides sur un
    module sans licence active. Purement informatif : la suppression du compte n'est jamais
    conditionnée à ce que montre cette liste.
    """
    supports = {
        sub.module_id: sub
        for sub in SupportSubscription.objects.filter(user=user, expires_at__gt=timezone.now()).select_related('module')
    }
    license_refunds = _license_refunds(user)
    holdings = []
    for lic in License.objects.filter(user=user, is_active=True).select_related('module').order_by('module__name'):
        support = supports.pop(lic.module_id, None)
        holdings.append({
            'module': lic.module,
            'license_key': lic.license_key,
            'support_until': support.expires_at if support else None,
            'refund': _support_refund_due(user, lic.module) if support else None,
            'license_refund': license_refunds.get(lic.pk),
        })
    for support in supports.values():
        holdings.append({
            'module': support.module,
            'license_key': None,
            'support_until': support.expires_at,
            'refund': _support_refund_due(user, support.module),
            'license_refund': None,
        })
    return holdings


def refunds_due(holdings):
    """Remboursements à consigner : supports, puis licences (un pack n'est compté qu'une fois)."""
    refunds = [h['refund'] for h in holdings if h['refund']]
    seen = set()
    for h in holdings:
        refund = h['license_refund']
        if refund and refund['item'].pk not in seen:
            seen.add(refund['item'].pk)
            refunds.append(refund)
    return refunds


def _record_refunds(refunds):
    """Consigne chaque remboursement sur sa ligne de commande ; une commande peut en porter plusieurs."""
    by_order = {}
    for refund in refunds:
        by_order.setdefault(refund['order'].pk, (refund['order'], []))[1].append(
            (refund['item'], refund['amount'], refund['reason']))
    for order, lines in by_order.values():
        order.record_refunds(lines)


@login_required
def delete_account_confirm(request):
    """
    Affiche la page de confirmation de suppression de compte (GET)
    et désactive le compte (POST).

    Conformément à l'Art. 17 RGPD, les données d'identification sont effacées : le compte est
    désactivé immédiatement, puis anonymisé par la commande planifiée anonymize_deleted_accounts
    après ACCOUNT_ANONYMIZATION_DELAY_DAYS jours. Les commandes et licences sont conservées
    (obligation fiscale Art. 17.3.b).
    La suppression n'est jamais refusée, quels que soient les produits ou services en cours :
    le client en est seulement informé. Dans les 14 jours suivant la commande, le remboursement
    dû est calculé et consigné sur la ligne de commande pour un traitement manuel par l'équipe :
    support au prorata (droit de rétractation, Art. VI.51 CDE), licence jamais activée ou achetée
    sans renonciation au prix payé. Les licences remboursées sont désactivées dans la même
    transaction. Passé ce délai, rien n'est dû.
    """
    holdings = account_holdings(request.user)
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation', '')
        if confirmation != 'SUPPRIMER':
            messages.error(request, _("Confirmation incorrecte. Veuillez saisir SUPPRIMER pour confirmer."))
            return redirect('users:delete_account_confirm')
        refunds = refunds_due(holdings)
        refunded_licenses = [lic.pk for r in refunds for lic in r.get('licenses', [])]
        with transaction.atomic():
            _record_refunds(refunds)
            # Une licence remboursée est désactivée : le Core ne peut plus l'activer ni la télécharger.
            License.objects.filter(pk__in=refunded_licenses).update(is_active=False)
            user = request.user
            user.soft_delete()
        delay = settings.ACCOUNT_ANONYMIZATION_DELAY_DAYS
        audit_logger.info(
            f"ACCOUNT DELETION SUCCESS: User {user.username} (ID: {user.pk}) deleted their account "
            f"(deactivated, anonymization scheduled after {delay} days; orders and licenses kept; "
            f"refunds due: {len(refunds)}; licenses deactivated after refund: {len(refunded_licenses)})."
        )
        logout(request)
        message = _("Votre compte a été désactivé. Vos données personnelles seront définitivement anonymisées "
                    "dans un délai de %(days)s jours.") % {'days': delay}
        if refunds:
            support = sum((r['amount'] for r in refunds if r['reason'] == 'withdrawal_support'), Decimal('0'))
            licenses = sum((r['amount'] for r in refunds if r['reason'] != 'withdrawal_support'), Decimal('0'))
            message = f"{message} " + _(
                "Un remboursement de %(total)s € sera traité par notre équipe : %(support)s € pour le support "
                "(droit de rétractation) et %(licenses)s € pour les licences.") % {
                'total': number_format(support + licenses, 2),
                'support': number_format(support, 2),
                'licenses': number_format(licenses, 2),
            }
        messages.success(request, message)
        return redirect('core:home')

    return render(request, 'account/delete_account_confirm.html', {
        'title': _("Supprimer mon compte"),
        'holdings': holdings,
        'refund_total': sum((r['amount'] for r in refunds_due(holdings)), Decimal('0')),
        'anonymization_delay_days': settings.ACCOUNT_ANONYMIZATION_DELAY_DAYS,
    })

"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : backoffice
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Vues pour l'administration personnalisée (Backoffice).
              Calcul des statistiques globales et gestion des entités métiers.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import models
import datetime
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from .pagination import paginate
from .filters import FilterSet, Search, Choice, Bool, ModelChoice, DateRange, NumberRange
from payments.models import Order, OrderItem
from licensing.models import License, Installation, SupportSubscription
from catalog.models import Module, ModuleBundle, Category, ModuleVersion, CoreVersion
from .forms import (
    ModuleForm, CategoryForm, ModuleBundleForm, ModuleVersionForm, CoreVersionForm,
    SupportSubscriptionSearchForm,
)
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

User = get_user_model()

# Définition du FormSet pour les versions
ModuleVersionFormSet = inlineformset_factory(
    Module, ModuleVersion, form=ModuleVersionForm, extra=1, can_delete=True
)


def is_admin(user):
    """Vérifie si l'utilisateur est un administrateur."""
    return user.is_superuser

@user_passes_test(is_admin)
def index(request):
    """
    Vue principale du Backoffice affichant les statistiques globales.
    """
    total_products = Module.objects.count()
    total_earnings = Order.objects.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_licenses = License.objects.count()
    total_sales = Order.objects.filter(status='completed').count()
    
    # Dernières transactions
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    context = {
        'total_products': total_products,
        'total_earnings': total_earnings,
        'total_licenses': total_licenses,
        'total_sales': total_sales,
        'recent_orders': recent_orders,
        'admin_name': request.user.username
    }
    
    return render(request, 'backoffice/index.html', context)

@user_passes_test(is_admin)
def module_list(request):
    """
    Affiche la liste des modules avec leurs statistiques de performance.
    """
    modules = Module.objects.all().annotate(
        sales_count=Count('orderitem', filter=Q(orderitem__order__status='completed')),
        total_revenue=Sum('orderitem__price_at_purchase', filter=Q(orderitem__order__status='completed'))
    )
    
    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=[
            'name_fr', 'name_en', 'name_nl', 'slug_fr', 'short_description_fr', 'short_description_en', 'short_description_nl']),
        ModelChoice('category', _("Catégorie"), Category.objects.all(), field='category'),
        Bool('active', _("Actif"), field='is_active'),
        Choice('sales', _("Ventes"), [('yes', _("Avec ventes")), ('no', _("Sans vente"))],
               apply=lambda qs, v: qs.filter(sales_count__gt=0) if v == 'yes' else qs.filter(sales_count=0)),
        Bool('support', _("Support annuel proposé"), apply=lambda qs, yes: qs.filter(support_annual_price__isnull=not yes)),
        NumberRange('price', _("Prix (€)"), field='price'),
        DateRange('created', _("Date de création"), field='created_at'),
    ])
    page = paginate(request, filters.apply(modules).order_by('pk'))
    context = {
        'modules': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/modules.html', context)

def _bundle_validity(queryset, value):
    """Filtre les packs selon leur période de validité (une date vide signifie « sans limite »)."""
    now = timezone.now()
    started = Q(start_date__isnull=True) | Q(start_date__lte=now)
    not_ended = Q(end_date__isnull=True) | Q(end_date__gte=now)
    if value == 'current':
        return queryset.filter(started, not_ended)
    if value == 'upcoming':
        return queryset.filter(start_date__gt=now)
    if value == 'expired':
        return queryset.filter(end_date__lt=now)
    return queryset.filter(start_date__isnull=True, end_date__isnull=True)


@user_passes_test(is_admin)
def bundle_list(request):
    """
    Affiche la liste des packs (bundles) avec leurs statistiques de performance.
    """
    bundles = ModuleBundle.objects.all().annotate(
        sales_count=Count('orderitem', filter=Q(orderitem__order__status='completed')),
        total_revenue=Sum('orderitem__price_at_purchase', filter=Q(orderitem__order__status='completed'))
    )
    
    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=[
            'name_fr', 'name_en', 'name_nl', 'slug_fr', 'short_description_fr', 'short_description_en', 'short_description_nl']),
        Bool('active', _("Actif"), field='is_active'),
        Choice('discount', _("Mode de remise"), ModuleBundle.DISCOUNT_MODES, field='discount_mode'),
        Choice('validity', _("Validité"), [
            ('current', _("En cours")), ('upcoming', _("À venir")), ('expired', _("Expirée")), ('unlimited', _("Sans limite"))],
            apply=_bundle_validity),
        ModelChoice('module', _("Module inclus"), Module.objects.all(),
                    apply=lambda qs, pk: qs.filter(pk__in=ModuleBundle.objects.filter(modules=pk).values('pk'))),
        Choice('sales', _("Ventes"), [('yes', _("Avec ventes")), ('no', _("Sans vente"))],
               apply=lambda qs, v: qs.filter(sales_count__gt=0) if v == 'yes' else qs.filter(sales_count=0), advanced=True),
        DateRange('starts', _("Début de validité"), field='start_date'),
    ])
    page = paginate(request, filters.apply(bundles).order_by('pk'))
    context = {
        'bundles': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/bundles.html', context)

@user_passes_test(is_admin)
def license_list(request):
    """
    Affiche la liste complète des licences accordées.
    Vue de monitoring pour le suivi des activations premium.
    """
    licenses = License.objects.all().select_related('user', 'module').order_by('-created_at')
    
    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=[
            'license_key', 'user__username', 'user__email', 'module__name_fr', 'module__name_en', 'module__name_nl'],
            id_field='id', hex_fields=['license_key']),
        ModelChoice('module', _("Module"), Module.objects.all(), field='module'),
        Bool('active', _("Licence active"), field='is_active'),
        Choice('activations', _("Activations"), [('available', _("Disponibles")), ('full', _("Épuisées"))],
               apply=lambda qs, v: qs.filter(activation_count__lt=F('max_activations')) if v == 'available'
               else qs.filter(activation_count__gte=F('max_activations'))),
        Bool('installed', _("Rattachée à une installation"),
             apply=lambda qs, yes: qs.filter(installation__isnull=not yes), advanced=True),
        DateRange('purchased', _("Date d'achat"), field='created_at'),
    ])
    page = paginate(request, filters.apply(licenses))
    context = {
        'licenses': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/licenses.html', context)

@user_passes_test(is_admin)
def installation_list(request):
    """
    Affiche la liste des machines clientes (installations) enregistrées.
    Permet de monitorer quel client utilise quelle machine (UUID).
    """
    installations = Installation.objects.all().select_related('user').prefetch_related('licenses__module').order_by('-last_sync')
    
    versions = sorted(set(Installation.objects.values_list('core_version', flat=True)))
    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=['installation_uuid', 'company_name', 'user__username', 'user__email'],
               id_field='id', hex_fields=['installation_uuid']),
        Choice('core', _("Version du Core"), [(v, v) for v in versions], field='core_version'),
        Bool('linked', _("Compte lié"), apply=lambda qs, yes: qs.filter(user__isnull=not yes)),
        Bool('licensed', _("Avec licences"),
             apply=lambda qs, yes: qs.filter(pk__in=License.objects.exclude(installation=None).values('installation'))
             if yes else qs.exclude(pk__in=License.objects.exclude(installation=None).values('installation')), advanced=True),
        DateRange('synced', _("Dernière synchronisation"), field='last_sync'),
    ])
    page = paginate(request, filters.apply(installations))
    context = {
        'installations': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/installations.html', context)

@user_passes_test(is_admin)
def module_create(request):
    """Vue pour la création d'un nouveau module avec sa version."""
    if request.method == 'POST':
        form = ModuleForm(request.POST, request.FILES)
        formset = ModuleVersionFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            module = form.save()
            versions = formset.save(commit=False)
            for version in versions:
                version.module = module
                version.save()
            messages.success(request, _("Le module '%(name)s' et sa version ont été créés.") % {'name': module.name})
            return redirect('backoffice:module_list')
    else:
        form = ModuleForm()
        formset = ModuleVersionFormSet()
    
    return render(request, 'backoffice/module_form.html', {
        'form': form,
        'formset': formset,
        'title': _("Créer un Module"),
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def module_edit(request, pk):
    """Vue pour la modification d'un module et de ses versions."""
    module = get_object_or_404(Module, pk=pk)
    if request.method == 'POST':
        form = ModuleForm(request.POST, request.FILES, instance=module)
        formset = ModuleVersionFormSet(request.POST, request.FILES, instance=module)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _("Le module '%(name)s' a été mis à jour.") % {'name': module.name})
            return redirect('backoffice:module_list')
    else:
        form = ModuleForm(instance=module)
        formset = ModuleVersionFormSet(instance=module)
    
    return render(request, 'backoffice/module_form.html', {
        'form': form,
        'formset': formset,
        'module': module,
        'title': _("Modifier %(name)s") % {'name': module.name},
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def module_delete(request, pk):
    """Vue pour la suppression d'un module."""
    module = get_object_or_404(Module, pk=pk)
    if request.method == 'POST':
        name = module.name
        module.delete()
        messages.warning(request, _("Le module '%(name)s' a été supprimé.") % {'name': name})
        return redirect('backoffice:module_list')
    
    return render(request, 'backoffice/module_confirm_delete.html', {
        'module': module,
        'admin_name': request.user.username
    })

# --- CRUD CATÉGORIES ---

@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.all().annotate(modules_count=Count('modules'))
    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=['name_fr', 'name_en', 'name_nl', 'slug_fr']),
        Choice('modules', _("Modules"), [('with', _("Avec modules")), ('without', _("Sans module"))],
               apply=lambda qs, v: qs.filter(modules_count__gt=0) if v == 'with' else qs.filter(modules_count=0)),
        NumberRange('count', _("Nombre de modules"), field='modules_count'),
    ])
    page = paginate(request, filters.apply(categories).order_by('pk'))
    return render(request, 'backoffice/category_list.html', {
        'categories': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, _("Catégorie '%(name)s' créée.") % {'name': cat.name})
            return redirect('backoffice:category_list')
    else:
        form = CategoryForm()
    return render(request, 'backoffice/category_form.html', {'form': form, 'title': _("Nouvelle Catégorie"), 'admin_name': request.user.username})

@user_passes_test(is_admin)
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie mise à jour."))
            return redirect('backoffice:category_list')
    else:
        form = CategoryForm(instance=cat)
    return render(request, 'backoffice/category_form.html', {'form': form, 'cat': cat, 'title': _("Modifier Catégorie"), 'admin_name': request.user.username})

@user_passes_test(is_admin)
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.warning(request, _("Catégorie supprimée."))
        return redirect('backoffice:category_list')
    return render(request, 'backoffice/category_confirm_delete.html', {'cat': cat, 'admin_name': request.user.username})


# --- CRUD PACKS (BUNDLES) ---

@user_passes_test(is_admin)
def bundle_create(request):
    if request.method == 'POST':
        form = ModuleBundleForm(request.POST, request.FILES)
        if form.is_valid():
            bundle = form.save()
            messages.success(request, _("Pack '%(name)s' créé.") % {'name': bundle.name})
            return redirect('backoffice:bundle_list')
    else:
        form = ModuleBundleForm()
    return render(request, 'backoffice/bundle_form.html', {'form': form, 'title': _("Nouveau Pack"), 'admin_name': request.user.username})

@user_passes_test(is_admin)
def bundle_edit(request, pk):
    bundle = get_object_or_404(ModuleBundle, pk=pk)
    if request.method == 'POST':
        form = ModuleBundleForm(request.POST, request.FILES, instance=bundle)
        if form.is_valid():
            form.save()
            messages.success(request, _("Pack mis à jour."))
            return redirect('backoffice:bundle_list')
    else:
        form = ModuleBundleForm(instance=bundle)
    return render(request, 'backoffice/bundle_form.html', {'form': form, 'bundle': bundle, 'title': _("Modifier Pack"), 'admin_name': request.user.username})

@user_passes_test(is_admin)
def bundle_delete(request, pk):
    bundle = get_object_or_404(ModuleBundle, pk=pk)
    if request.method == 'POST':
        bundle.delete()
        messages.warning(request, _("Pack supprimé."))
        return redirect('backoffice:bundle_list')
    return render(request, 'backoffice/bundle_confirm_delete.html', {'bundle': bundle, 'admin_name': request.user.username})

# --- CRUD VERSIONS CORE ---

@user_passes_test(is_admin)
def core_version_list(request):
    versions = CoreVersion.objects.all().order_by('-version')
    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=['version']),
        Bool('active', _("Version supportée"), field='is_active'),
        DateRange('released', _("Date de sortie"), field='release_date'),
    ])
    page = paginate(request, filters.apply(versions))
    return render(request, 'backoffice/core_version_list.html', {
        'versions': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def core_version_create(request):
    if request.method == 'POST':
        form = CoreVersionForm(request.POST)
        if form.is_valid():
            v = form.save()
            messages.success(request, _("Version Core '%(version)s' créée.") % {'version': v.version})
            return redirect('backoffice:core_version_list')
    else:
        form = CoreVersionForm()
    return render(request, 'backoffice/core_version_form.html', {'form': form, 'title': _("Nouvelle Version Core"), 'admin_name': request.user.username})

@user_passes_test(is_admin)
def core_version_edit(request, pk):
    v = get_object_or_404(CoreVersion, pk=pk)
    if request.method == 'POST':
        form = CoreVersionForm(request.POST, instance=v)
        if form.is_valid():
            form.save()
            messages.success(request, _("Version Core mise à jour."))
            return redirect('backoffice:core_version_list')
    else:
        form = CoreVersionForm(instance=v)
    return render(request, 'backoffice/core_version_form.html', {'form': form, 'v': v, 'title': _("Modifier Version Core"), 'admin_name': request.user.username})

@user_passes_test(is_admin)
def core_version_delete(request, pk):
    v = get_object_or_404(CoreVersion, pk=pk)
    if request.method == 'POST':
        v.delete()
        messages.warning(request, _("Version Core supprimée."))
        return redirect('backoffice:core_version_list')
    return render(request, 'backoffice/core_version_confirm_delete.html', {'v': v, 'admin_name': request.user.username})

# --- GESTION DES UTILISATEURS / CLIENTS ---

def _user_type(queryset, value):
    """Type de compte : client, staff (hors super-utilisateur) ou super-utilisateur."""
    if value == 'client':
        return queryset.filter(is_client=True)
    if value == 'staff':
        return queryset.filter(is_staff=True, is_superuser=False)
    return queryset.filter(is_superuser=True)


def _user_status(queryset, value):
    """Statut du compte : actif, désactivé, ou supprimé (anonymisé selon l'article 17 du RGPD)."""
    if value == 'active':
        return queryset.filter(is_active=True, is_deleted=False)
    if value == 'disabled':
        return queryset.filter(is_active=False, is_deleted=False)
    return queryset.filter(is_deleted=True)


@user_passes_test(is_admin)
def user_list(request):
    """Affiche la liste des clients et leurs statistiques."""
    users = User.objects.all().annotate(
        license_count=Count('licenses', distinct=True),
        order_count=Count('orders', distinct=True)
    ).order_by('-date_joined')
    
    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=['username', 'email', 'first_name', 'last_name'], id_field='id'),
        Choice('type', _("Type de compte"), [('client', _("Client")), ('staff', _("Staff")), ('admin', _("Super-utilisateur"))],
               apply=_user_type),
        Choice('status', _("Statut du compte"), [
            ('active', _("Actif")), ('disabled', _("Désactivé")), ('deleted', _("Supprimé (anonymisé)"))], apply=_user_status),
        Choice('language', _("Langue"), User._meta.get_field('language_preference').choices, field='language_preference'),
        Choice('licenses', _("Licences"), [('with', _("Avec licences")), ('without', _("Sans licence"))],
               apply=lambda qs, v: qs.filter(license_count__gt=0) if v == 'with' else qs.filter(license_count=0), advanced=True),
        Choice('orders', _("Commandes"), [('with', _("Avec commandes")), ('without', _("Sans commande"))],
               apply=lambda qs, v: qs.filter(order_count__gt=0) if v == 'with' else qs.filter(order_count=0), advanced=True),
        DateRange('joined', _("Date d'inscription"), field='date_joined'),
    ])
    page = paginate(request, filters.apply(users))
    return render(request, 'backoffice/user_list.html', {
        'users': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def user_detail(request, pk):
    """Vue détaillée d'un client avec tout son historique."""
    u = get_object_or_404(User, pk=pk)
    
    # Récupération des données liées
    orders = Order.objects.filter(user=u).order_by('-created_at')
    licenses = License.objects.filter(user=u).select_related('module').order_by('-created_at')
    installations = Installation.objects.filter(user=u).prefetch_related('licenses__module').order_by('-last_sync')
    support_subscriptions = SupportSubscription.objects.filter(user=u).select_related('module').order_by('module__name')

    # Statistiques rapides
    total_spent = orders.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    return render(request, 'backoffice/user_detail.html', {
        'u': u,
        'orders': orders,
        'licenses': licenses,
        'installations': installations,
        'support_subscriptions': support_subscriptions,
        'total_spent': total_spent,
        'admin_name': request.user.username
    })


@user_passes_test(is_admin)
def support_subscription_search(request):
    """
    Support Client : recherche d'un client par email (pour traiter une demande entrante),
    et liste des clients ayant au moins un abonnement support, avec leur nombre de licences
    support (actives / total). Un clic sur une ligne mène a la fiche client.
    """
    form = SupportSubscriptionSearchForm(request.GET or None)
    not_found_email = None
    if form.is_valid() and form.cleaned_data['email']:
        email = form.cleaned_data['email']
        found_user = User.objects.filter(email__iexact=email).first()
        if found_user:
            return redirect('backoffice:user_detail', pk=found_user.pk)
        not_found_email = email

    clients = User.objects.annotate(
        support_active_count=Count(
            'support_subscriptions',
            filter=Q(support_subscriptions__expires_at__gt=timezone.now()),
            distinct=True
        ),
        support_total_count=Count('support_subscriptions', distinct=True),
    ).filter(support_total_count__gt=0).order_by('-support_active_count', '-support_total_count', 'username')

    now = timezone.now()
    filters = FilterSet(request, [
        Search('q', _("Filtrer les clients"), fields=['username', 'email', 'first_name', 'last_name'], id_field='id'),
        Choice('support', _("Abonnement"), [('active', _("Actif")), ('expired', _("Expiré"))],
               apply=lambda qs, v: qs.filter(support_active_count__gt=0) if v == 'active' else qs.filter(support_active_count=0)),
        ModelChoice('module', _("Module"), Module.objects.all(),
                    apply=lambda qs, pk: qs.filter(pk__in=SupportSubscription.objects.filter(module=pk).values('user'))),
        Choice('expiring', _("Échéance"), [('30', _("Expire dans 30 jours")), ('90', _("Expire dans 90 jours"))],
               apply=lambda qs, days: qs.filter(pk__in=SupportSubscription.objects.filter(
                   expires_at__gt=now, expires_at__lte=now + datetime.timedelta(days=int(days))).values('user')), advanced=True),
    ])
    page = paginate(request, filters.apply(clients))
    return render(request, 'backoffice/support_subscription_search.html', {
        'filters': filters,
        'form': form,
        'not_found_email': not_found_email,
        'clients': page,
        'page': page,
        'admin_name': request.user.username,
    })

# --- SUIVI DES TRANSACTIONS ---

@user_passes_test(is_admin)
def module_sales(request, pk):
    """
    Détail des ventes d'un module : qui l'a acheté, quand, à quel prix, avec quelle licence.
    Inclut les achats directs, le support annuel et les achats via un pack.
    Recherche par email, nom d'utilisateur, n° de commande ou référence de paiement.
    """
    module = get_object_or_404(Module, pk=pk)

    base = OrderItem.objects.filter(Q(module=module) | Q(bundle__modules=module)).distinct()

    items = (
        base
        .select_related('order', 'order__user', 'bundle')
        .order_by('-order__created_at', '-id')
    )

    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=[
            'order__user__email', 'order__user__username', 'order__stripe_payment_intent_id'], id_field='order_id'),
        Choice('type', _("Type de vente"), [('module', _("Module")), ('pack', _("Pack")), ('support', _("Support annuel"))],
               apply=lambda qs, v: qs.filter(bundle__isnull=False) if v == 'pack'
               else qs.filter(bundle__isnull=True, product_type=v)),
        Choice('status', _("Statut"), Order.STATUS_CHOICES, field='order__status'),
        DateRange('date', _("Date de la vente"), field='order__created_at'),
    ])
    items = filters.apply(items)
    query = filters.values['q'] or ''

    # Les statistiques portent sur toutes les ventes du module, indépendamment de la recherche.
    completed = base.filter(order__status='completed')
    direct = completed.filter(module=module, product_type='module')
    stats = {
        'direct_count': direct.count(),
        'bundle_count': completed.filter(module__isnull=True).count(),
        'support_count': completed.filter(module=module, product_type='support').count(),
        'direct_revenue': direct.aggregate(total=Sum('price_at_purchase'))['total'] or 0,
        'buyers_count': completed.values('order__user').distinct().count(),
        'refunded_count': base.filter(order__status='refunded').count(),
    }

    page = paginate(request, items)

    # Licence de chaque acheteur pour ce module (une clé par utilisateur et module).
    user_ids = {item.order.user_id for item in page}
    licenses = {
        lic.user_id: lic
        for lic in License.objects.filter(module=module, user_id__in=user_ids)
    }
    for item in page:
        item.license = licenses.get(item.order.user_id)

    return render(request, 'backoffice/module_sales.html', {
        'module': module,
        'page': page,
        'query': query,
        'filters': filters,
        'stats': stats,
        'admin_name': request.user.username,
    })

@user_passes_test(is_admin)
def order_list(request):
    """Affiche l'historique complet des transactions (Commandes)."""
    orders = Order.objects.all().select_related('user').prefetch_related('items__module').order_by('-created_at')

    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=['user__username', 'user__email', 'stripe_payment_intent_id'], id_field='id'),
        Choice('status', _("Statut"), Order.STATUS_CHOICES, field='status'),
        ModelChoice('module', _("Module acheté"), Module.objects.all(),
                    apply=lambda qs, pk: qs.filter(pk__in=OrderItem.objects.filter(module=pk).values('order_id'))),
        DateRange('created', _("Date de la commande"), field='created_at'),
        NumberRange('amount', _("Montant (€)"), field='total_amount'),
        ModelChoice('bundle', _("Pack acheté"), ModuleBundle.objects.all(),
                    apply=lambda qs, pk: qs.filter(pk__in=OrderItem.objects.filter(bundle=pk).values('order_id')), advanced=True),
        Bool('waiver', _("Renonciation à la rétractation"),
             apply=lambda qs, yes: qs.filter(withdrawal_waiver_accepted_at__isnull=not yes), advanced=True),
    ])
    page = paginate(request, filters.apply(orders))
    return render(request, 'backoffice/order_list.html', {
        'orders': page,
        'page': page,
        'filters': filters,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def order_detail(request, pk):
    """Vue détaillée d'une transaction."""
    order = get_object_or_404(Order.objects.select_related('user'), pk=pk)
    items = order.items.all().select_related('module')
    
    return render(request, 'backoffice/order_detail.html', {
        'order': order,
        'items': items,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def logs_view(request):
    """
    Affiche le fichier de logs d'audit dans le backoffice personnalisé.
    """
    import os
    from django.conf import settings
    from .models import DatabaseAuditLog
    
    log_path = settings.BASE_DIR / 'logs' / 'audit.log'
    log_content = ""
    
    # Action de vidage (clear)
    if request.GET.get('action') == 'clear':
        try:
            if os.path.exists(log_path):
                with open(log_path, 'w') as f:
                    f.write("")
            DatabaseAuditLog.objects.all().delete()
            messages.success(request, _("Les logs applicatifs et de base de données ont été vidés avec succès."))
            return redirect('backoffice:logs_view')
        except Exception as e:
            messages.error(request, _("Erreur lors du vidage des logs : %(error)s") % {'error': str(e)})
            
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                # Lire les 200 dernières lignes pour des raisons de performance et de lisibilite
                lines = f.readlines()
                log_content = "".join(lines[-200:])
        except Exception as e:
            log_content = _("Erreur lors de la lecture du fichier de logs : %(error)s") % {'error': str(e)}
    else:
        log_content = _("Le fichier de logs n'existe pas encore. L'activité générera ce fichier.")
        
    # Charger les logs de base de données insérés par les triggers
    db_logs = paginate(request, DatabaseAuditLog.objects.all().order_by('-timestamp'))
        
    context = {
        'log_content': log_content,
        'db_logs': db_logs,
        'page': db_logs,
        'title': _("Visualiseur de Logs d'Audit"),
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/logs.html', context)

@user_passes_test(is_admin)
def reviews_list(request):
    """
    Lister tous les avis clients pour modération dans le backoffice.
    """
    from catalog.models import Review
    reviews = Review.objects.all().select_related('user', 'module', 'bundle')
    
    pending_count = Review.objects.filter(is_approved=False).count()
    approved_count = Review.objects.filter(is_approved=True).count()
    
    page = paginate(request, reviews)
    context = {
        'reviews': page,
        'page': page,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'title': _("Modération des Avis Clients"),
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/reviews.html', context)

@user_passes_test(is_admin)
def review_approve(request, pk):
    """
    Approuver un avis client (ce qui déclenche la traduction automatique via LibreTranslate).
    """
    from catalog.models import Review
    review = get_object_or_404(Review, pk=pk)
    if not review.is_approved:
        review.is_approved = True
        review.save()  # Le signal save déclenche la traduction automatique via LibreTranslate
        messages.success(request, _("L'avis de %(name)s a été approuvé et traduit avec succès.") % {'name': review.user.username})
    else:
        messages.warning(request, _("Cet avis est déjà approuvé."))
    return redirect('backoffice:reviews_list')

@user_passes_test(is_admin)
def review_delete(request, pk):
    """
    Rejeter ou supprimer un avis client.
    """
    from catalog.models import Review
    review = get_object_or_404(Review, pk=pk)
    username = review.user.username
    review.delete()
    messages.success(request, _("L'avis de %(name)s a été rejeté/supprimé avec succès.") % {'name': username})
    return redirect('backoffice:reviews_list')

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
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from core.models import ContactMessage
from payments.models import Order, OrderItem
from licensing.models import License, Installation, SupportSubscription
from catalog.models import Module, ModuleBundle, Category, ModuleVersion, CoreVersion
from .forms import (
    ModuleForm, CategoryForm, ModuleBundleForm, ModuleVersionForm, CoreVersionForm, UserEditForm,
    SupportSubscriptionSearchForm,
)
from django.contrib.auth import get_user_model

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
    
    context = {
        'modules': modules,
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/modules.html', context)

@user_passes_test(is_admin)
def bundle_list(request):
    """
    Affiche la liste des packs (bundles) avec leurs statistiques de performance.
    """
    bundles = ModuleBundle.objects.all().annotate(
        sales_count=Count('orderitem', filter=Q(orderitem__order__status='completed')),
        total_revenue=Sum('orderitem__price_at_purchase', filter=Q(orderitem__order__status='completed'))
    )
    
    context = {
        'bundles': bundles,
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
    
    context = {
        'licenses': licenses,
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
    
    context = {
        'installations': installations,
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
            messages.success(request, f"Le module '{module.name}' et sa version ont été créés.")
            return redirect('backoffice:module_list')
    else:
        form = ModuleForm()
        formset = ModuleVersionFormSet()
    
    return render(request, 'backoffice/module_form.html', {
        'form': form,
        'formset': formset,
        'title': "Créer un Module",
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
            messages.success(request, f"Le module '{module.name}' a été mis à jour.")
            return redirect('backoffice:module_list')
    else:
        form = ModuleForm(instance=module)
        formset = ModuleVersionFormSet(instance=module)
    
    return render(request, 'backoffice/module_form.html', {
        'form': form,
        'formset': formset,
        'module': module,
        'title': f"Modifier {module.name}",
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def module_delete(request, pk):
    """Vue pour la suppression d'un module."""
    module = get_object_or_404(Module, pk=pk)
    if request.method == 'POST':
        name = module.name
        module.delete()
        messages.warning(request, f"Le module '{name}' a été supprimé.")
        return redirect('backoffice:module_list')
    
    return render(request, 'backoffice/module_confirm_delete.html', {
        'module': module,
        'admin_name': request.user.username
    })

# --- CRUD CATÉGORIES ---

@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.all().annotate(modules_count=Count('modules'))
    return render(request, 'backoffice/category_list.html', {
        'categories': categories,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Catégorie '{cat.name}' créée.")
            return redirect('backoffice:category_list')
    else:
        form = CategoryForm()
    return render(request, 'backoffice/category_form.html', {'form': form, 'title': "Nouvelle Catégorie", 'admin_name': request.user.username})

@user_passes_test(is_admin)
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie mise à jour.")
            return redirect('backoffice:category_list')
    else:
        form = CategoryForm(instance=cat)
    return render(request, 'backoffice/category_form.html', {'form': form, 'cat': cat, 'title': "Modifier Catégorie", 'admin_name': request.user.username})

@user_passes_test(is_admin)
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.warning(request, "Catégorie supprimée.")
        return redirect('backoffice:category_list')
    return render(request, 'backoffice/category_confirm_delete.html', {'cat': cat, 'admin_name': request.user.username})


# --- CRUD PACKS (BUNDLES) ---

@user_passes_test(is_admin)
def bundle_create(request):
    if request.method == 'POST':
        form = ModuleBundleForm(request.POST, request.FILES)
        if form.is_valid():
            bundle = form.save()
            messages.success(request, f"Pack '{bundle.name}' créé.")
            return redirect('backoffice:bundle_list')
    else:
        form = ModuleBundleForm()
    return render(request, 'backoffice/bundle_form.html', {'form': form, 'title': "Nouveau Pack", 'admin_name': request.user.username})

@user_passes_test(is_admin)
def bundle_edit(request, pk):
    bundle = get_object_or_404(ModuleBundle, pk=pk)
    if request.method == 'POST':
        form = ModuleBundleForm(request.POST, request.FILES, instance=bundle)
        if form.is_valid():
            form.save()
            messages.success(request, "Pack mis à jour.")
            return redirect('backoffice:bundle_list')
    else:
        form = ModuleBundleForm(instance=bundle)
    return render(request, 'backoffice/bundle_form.html', {'form': form, 'bundle': bundle, 'title': "Modifier Pack", 'admin_name': request.user.username})

@user_passes_test(is_admin)
def bundle_delete(request, pk):
    bundle = get_object_or_404(ModuleBundle, pk=pk)
    if request.method == 'POST':
        bundle.delete()
        messages.warning(request, "Pack supprimé.")
        return redirect('backoffice:bundle_list')
    return render(request, 'backoffice/bundle_confirm_delete.html', {'bundle': bundle, 'admin_name': request.user.username})

# --- CRUD VERSIONS CORE ---

@user_passes_test(is_admin)
def core_version_list(request):
    versions = CoreVersion.objects.all().order_by('-version')
    return render(request, 'backoffice/core_version_list.html', {
        'versions': versions,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def core_version_create(request):
    if request.method == 'POST':
        form = CoreVersionForm(request.POST)
        if form.is_valid():
            v = form.save()
            messages.success(request, f"Version Core '{v.version}' créée.")
            return redirect('backoffice:core_version_list')
    else:
        form = CoreVersionForm()
    return render(request, 'backoffice/core_version_form.html', {'form': form, 'title': "Nouvelle Version Core", 'admin_name': request.user.username})

@user_passes_test(is_admin)
def core_version_edit(request, pk):
    v = get_object_or_404(CoreVersion, pk=pk)
    if request.method == 'POST':
        form = CoreVersionForm(request.POST, instance=v)
        if form.is_valid():
            form.save()
            messages.success(request, "Version Core mise à jour.")
            return redirect('backoffice:core_version_list')
    else:
        form = CoreVersionForm(instance=v)
    return render(request, 'backoffice/core_version_form.html', {'form': form, 'v': v, 'title': "Modifier Version Core", 'admin_name': request.user.username})

@user_passes_test(is_admin)
def core_version_delete(request, pk):
    v = get_object_or_404(CoreVersion, pk=pk)
    if request.method == 'POST':
        v.delete()
        messages.warning(request, "Version Core supprimée.")
        return redirect('backoffice:core_version_list')
    return render(request, 'backoffice/core_version_confirm_delete.html', {'v': v, 'admin_name': request.user.username})

# --- GESTION DES UTILISATEURS / CLIENTS ---

@user_passes_test(is_admin)
def user_list(request):
    """Affiche la liste des clients et leurs statistiques."""
    users = User.objects.all().annotate(
        license_count=Count('licenses', distinct=True),
        order_count=Count('orders', distinct=True)
    ).order_by('-date_joined')
    
    return render(request, 'backoffice/user_list.html', {
        'users': users,
        'admin_name': request.user.username
    })

@user_passes_test(is_admin)
def user_edit(request, pk):
    """Vue pour modifier un utilisateur/client."""
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'utilisateur '{u.username}' a été mis à jour.")
            return redirect('backoffice:user_list')
    else:
        form = UserEditForm(instance=u)
    return render(request, 'backoffice/user_form.html', {'form': form, 'u': u, 'title': "Modifier Client", 'admin_name': request.user.username})

@user_passes_test(is_admin)
def user_delete(request, pk):
    """Vue pour supprimer un utilisateur."""
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        name = u.username
        u.delete()
        messages.warning(request, f"L'utilisateur '{name}' a été supprimé.")
        return redirect('backoffice:user_list')
    return render(request, 'backoffice/user_confirm_delete.html', {'u': u, 'admin_name': request.user.username})

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

    return render(request, 'backoffice/support_subscription_search.html', {
        'form': form,
        'not_found_email': not_found_email,
        'clients': clients,
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

    query = (request.GET.get('q') or '').strip()
    if query:
        search = (
            Q(order__user__email__icontains=query)
            | Q(order__user__username__icontains=query)
            | Q(order__stripe_payment_intent_id__icontains=query)
        )
        if query.lstrip('#').isdigit():
            search |= Q(order_id=int(query.lstrip('#')))
        items = items.filter(search)

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

    page = Paginator(items, 50).get_page(request.GET.get('page'))

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
        'stats': stats,
        'admin_name': request.user.username,
    })

@user_passes_test(is_admin)
def order_list(request):
    """Affiche l'historique complet des transactions (Commandes)."""
    orders = Order.objects.all().select_related('user').prefetch_related('items__module').order_by('-created_at')
    
    return render(request, 'backoffice/order_list.html', {
        'orders': orders,
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
            messages.success(request, "Les logs applicatifs et de base de données ont été vidés avec succès.")
            return redirect('backoffice:logs_view')
        except Exception as e:
            messages.error(request, f"Erreur lors du vidage des logs : {str(e)}")
            
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                # Lire les 200 dernières lignes pour des raisons de performance et de lisibilite
                lines = f.readlines()
                log_content = "".join(lines[-200:])
        except Exception as e:
            log_content = f"Erreur lors de la lecture du fichier de logs : {str(e)}"
    else:
        log_content = "Le fichier de logs n'existe pas encore. L'activité générera ce fichier."
        
    # Charger les logs de base de données insérés par les triggers
    db_logs = DatabaseAuditLog.objects.all().order_by('-timestamp')[:100]
        
    context = {
        'log_content': log_content,
        'db_logs': db_logs,
        'title': "Visualiseur de Logs d'Audit",
        'admin_name': request.user.username
    }
    return render(request, 'backoffice/logs.html', context)

@user_passes_test(is_admin)
def contact_message_list(request):
    """Messages reçus via le formulaire de contact de la page d'accueil."""
    only_unread = request.GET.get('unread') == '1'
    contact_messages = ContactMessage.objects.all()
    if only_unread:
        contact_messages = contact_messages.filter(is_read=False)

    return render(request, 'backoffice/contact_messages.html', {
        'page': Paginator(contact_messages, 50).get_page(request.GET.get('page')),
        'only_unread': only_unread,
        'unread_count': ContactMessage.objects.filter(is_read=False).count(),
        'admin_name': request.user.username,
    })

@user_passes_test(is_admin)
@require_POST
def contact_message_toggle_read(request, pk):
    """Bascule un message entre lu et non lu."""
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    contact_message.is_read = not contact_message.is_read
    contact_message.save(update_fields=['is_read'])
    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = 'backoffice:contact_message_list'
    return redirect(next_url)

@user_passes_test(is_admin)
def reviews_list(request):
    """
    Lister tous les avis clients pour modération dans le backoffice.
    """
    from catalog.models import Review
    reviews = Review.objects.all().select_related('user', 'module', 'bundle')
    
    pending_count = Review.objects.filter(is_approved=False).count()
    approved_count = Review.objects.filter(is_approved=True).count()
    
    context = {
        'reviews': reviews,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'title': "Modération des Avis Clients",
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
        messages.success(request, f"L'avis de {review.user.username} a été approuvé et traduit avec succès.")
    else:
        messages.warning(request, "Cet avis est déjà approuvé.")
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
    messages.success(request, f"L'avis de {username} a été rejeté/supprimé avec succès.")
    return redirect('backoffice:reviews_list')

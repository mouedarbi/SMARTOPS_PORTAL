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
from payments.models import Order, OrderItem
from licensing.models import License, Installation
from catalog.models import Module, ModuleBundle, Category, ModuleVersion
from .forms import ModuleForm, CategoryForm, ModuleBundleForm, ModuleVersionForm
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

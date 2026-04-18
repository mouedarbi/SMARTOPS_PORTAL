"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : backoffice
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Vues pour l'administration personnalisée (Backoffice).
              Calcul des statistiques globales et gestion des entités métiers.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db import models
from django.db.models import Sum, Count, Q
from payments.models import Order, OrderItem
from licensing.models import License
from catalog.models import Module, ModuleBundle
from django.contrib.auth import get_user_model

User = get_user_model()

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

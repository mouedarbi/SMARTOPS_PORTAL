"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.2
Description : Vues pour l'intégration de Stripe.
              Gère la création de sessions Checkout et le traitement des Webhooks
              avec une approche robuste basée sur les attributs du SDK Stripe.
"""

import stripe
import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from catalog.models import Module
from .models import Order, OrderItem
from licensing.models import License
from django.contrib.auth import get_user_model

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request, module_id):
    """
    Crée une session Stripe Checkout pour l'achat d'un module.
    Utilise client_reference_id et metadata pour la réconciliation.
    """
    module = get_object_or_404(Module, id=module_id)
    
    success_url = request.build_absolute_uri(reverse('payments:payment_success')) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse('catalog:module_detail', kwargs={'slug': module.slug}))

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': module.name,
                        'description': module.short_description,
                    },
                    'unit_amount': int(module.price * 100),
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=request.user.email,
        # Référence client recommandée par Stripe
        client_reference_id=str(request.user.id),
        # Métadonnées pour le Webhook
        metadata={
            "user_id": str(request.user.id),
            "module_id": str(module.id),
        }
    )

    return redirect(checkout_session.url, code=303)

@login_required
def payment_success(request):
    """Vue de confirmation visuelle après paiement."""
    return render(request, 'payments/success.html', {'title': "Paiement Réussi"})

@csrf_exempt
def stripe_webhook(request):
    """
    Point d'entrée Webhook robuste utilisant l'accès par attributs
    pour traiter les objets StripeObject.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        print(f"WEBHOOK ERROR : {str(e)}")
        return HttpResponse(status=400)

    print(f"WEBHOOK REÇU : {event['type']}")

    if event['type'] == "checkout.session.completed":
        session = event['data']['object']

        # Accès direct [] recommandé pour les StripeObject
        user_id = session.metadata["user_id"] if session.metadata else None
        module_id = session.metadata["module_id"] if session.metadata else None

        # Backup via client_reference_id si besoin
        if not user_id and hasattr(session, 'client_reference_id'):
            user_id = session.client_reference_id

        print(f"WEBHOOK : User={user_id}, Module={module_id}")

        if not user_id or not module_id:
            print("WEBHOOK ERROR : Identifiants manquants (User ou Module)")
            return HttpResponse(status=200)

        # Logique de création en base de données
        try:
            user = User.objects.get(id=user_id)
            module = Module.objects.get(id=module_id)
            
            # Montant total en centimes converti en euros
            amount_total = getattr(session, 'amount_total', 0)
            
            order = Order.objects.create(
                user=user,
                status='completed',
                total_amount=amount_total / 100,
                stripe_payment_intent_id=getattr(session, 'payment_intent', None)
            )
            
            OrderItem.objects.create(
                order=order,
                module=module,
                price_at_purchase=module.price
            )
            
            License.objects.get_or_create(
                user=user,
                module=module,
                defaults={'is_active': True, 'max_activations': 1}
            )
            print(f"SUCCESS : Achat et Licence enregistrés pour {user.username}")
            
        except (User.DoesNotExist, Module.DoesNotExist) as e:
            print(f"WEBHOOK ERROR : Entité introuvable ({str(e)})")

    return HttpResponse(status=200)

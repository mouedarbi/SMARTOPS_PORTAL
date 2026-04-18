"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Vues pour l'intégration de Stripe.
              Gère la création de sessions Checkout et les redirections de succès/annulation.
"""

import stripe
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

# Configuration de la clé secrète Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request, module_id):
    """
    Crée une session Stripe Checkout pour l'achat d'un module spécifique.
    Redirige l'utilisateur vers la page de paiement Stripe.
    
    @param request: Objet HttpRequest.
    @param module_id: Identifiant du module à acheter.
    @return: Redirection vers Stripe Checkout.
    """
    module = get_object_or_404(Module, id=module_id)
    
    # Construction des URLs de retour
    # On utilise request.build_absolute_uri pour garantir des URLs complètes
    success_url = request.build_absolute_uri(reverse('payments:payment_success')) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse('catalog:module_detail', kwargs={'slug': module.slug}))

    # Création de la session Checkout
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
                    'unit_amount': int(module.price * 100), # Stripe utilise les centimes
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=request.user.email,
        metadata={
            'module_id': module.id,
            'user_id': request.user.id
        }
    )

    return redirect(checkout_session.url, code=303)

@login_required
def payment_success(request):
    """
    Vue affichée après un paiement réussi.
    En production, le traitement lourd est fait par Webhook, mais ici on confirme visuellement.
    
    @param request: Objet HttpRequest.
    @return: Rendu de la page de succès.
    """
    return render(request, 'payments/success.html', {'title': "Paiement Réussi"})


@csrf_exempt
def stripe_webhook(request):
    """
    Point d'entrée pour les notifications Stripe (Webhooks).
    Vérifie la signature et traite l'événement 'checkout.session.completed'.
    
    @param request: Objet HttpRequest contenant le payload de Stripe.
    @return: HttpResponse 200 si traité, 400 si erreur.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Traitement du paiement réussi
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Récupération des métadonnées envoyées lors de la création
        user_id = session['metadata'].get('user_id')
        module_id = session['metadata'].get('module_id')
        
        try:
            user = User.objects.get(id=user_id)
            module = Module.objects.get(id=module_id)
            
            # 1. Création de la commande
            order = Order.objects.create(
                user=user,
                status='completed',
                total_amount=session['amount_total'] / 100,
                stripe_payment_intent_id=session.get('payment_intent')
            )
            
            # 2. Ajout de l'item à la commande
            OrderItem.objects.create(
                order=order,
                module=module,
                price_at_purchase=module.price
            )
            
            # 3. Génération de la licence (Une seule licence par module/user pour l'instant)
            License.objects.get_or_create(
                user=user,
                module=module,
                defaults={
                    'is_active': True,
                    'max_activations': 1
                }
            )
            
        except (User.DoesNotExist, Module.DoesNotExist):
            pass

    return HttpResponse(status=200)

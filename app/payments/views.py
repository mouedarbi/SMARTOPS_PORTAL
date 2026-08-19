import stripe
import json
import logging
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from catalog.models import Module, ModuleBundle
from .models import Order, OrderItem
from licensing.models import License
from django.contrib.auth import get_user_model

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY
audit_logger = logging.getLogger('audit')

@login_required
def create_checkout_session(request, module_id):
    """
    Crée une session Stripe Checkout pour l'achat d'un module.
    Utilise client_reference_id et metadata pour la réconciliation.
    Capture également le consentement de renonciation au droit de rétractation.
    """
    module = get_object_or_404(Module, id=module_id)
    consent_timestamp = timezone.now()
    
    if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY.strip() == "":
        # Mode Démo / Simulation si Stripe n'est pas configuré
        order = Order.objects.create(
            user=request.user,
            status='pending',
            total_amount=module.price,
            withdrawal_waiver_accepted_at=consent_timestamp,
            stripe_payment_intent_id=f"mock_intent_mod_{module.id}_{request.user.id}"
        )
        OrderItem.objects.create(
            order=order,
            module=module,
            price_at_purchase=module.price
        )
        # Validation de non-vacuité avant finalisation
        if order.items.exists():
            order.status = 'completed'
            order.save()
            License.objects.create(
                user=request.user,
                module=module,
                is_active=True,
                max_activations=1
            )
        audit_logger.info(
            f"MOCK PURCHASE SUCCESS: User {request.user.username} (ID: {request.user.id}) successfully purchased Module {module.name} (ID: {module.id}) via Mock Checkout. License generated."
        )
        return redirect('payments:payment_success')
        
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
            "withdrawal_waiver_accepted_at": consent_timestamp.isoformat(),
        }
    )
    
    audit_logger.info(
        f"STRIPE CHECKOUT CREATED: User {request.user.username} (ID: {request.user.id}) created Stripe checkout session for Module {module.name} (ID: {module.id}). Session ID: {checkout_session.id}"
    )

    return redirect(checkout_session.url, code=303)

@login_required
def create_bundle_checkout_session(request, bundle_id):
    """
    Crée une session Stripe Checkout pour l'achat d'un pack (bundle) de modules.
    Capture également le consentement de renonciation au droit de rétractation.
    """
    bundle = get_object_or_404(ModuleBundle, id=bundle_id)
    consent_timestamp = timezone.now()
    
    if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY.strip() == "":
        # Mode Démo / Simulation si Stripe n'est pas configuré
        order = Order.objects.create(
            user=request.user,
            status='pending',
            total_amount=bundle.final_price,
            withdrawal_waiver_accepted_at=consent_timestamp,
            stripe_payment_intent_id=f"mock_intent_bundle_{bundle.id}_{request.user.id}"
        )
        OrderItem.objects.create(
            order=order,
            bundle=bundle,
            price_at_purchase=bundle.final_price
        )
        # Validation de non-vacuité via full_clean() avant finalisation
        if order.items.exists():
            order.status = 'completed'
            order.full_clean()
            order.save()
            for module in bundle.modules.all():
                License.objects.create(
                    user=request.user,
                    module=module,
                    is_active=True,
                    max_activations=1
                )
        audit_logger.info(
            f"MOCK BUNDLE PURCHASE SUCCESS: User {request.user.username} (ID: {request.user.id}) successfully purchased Bundle {bundle.name} (ID: {bundle.id}) via Mock Checkout. Licenses generated for {[m.name for m in bundle.modules.all()]}."
        )
        return redirect('payments:payment_success')
        
    success_url = request.build_absolute_uri(reverse('payments:payment_success')) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse('catalog:bundle_detail', kwargs={'slug': bundle.slug}))
    
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': bundle.name,
                        'description': bundle.short_description,
                    },
                    'unit_amount': int(bundle.final_price * 100),
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=request.user.email,
        client_reference_id=str(request.user.id),
        metadata={
            "user_id": str(request.user.id),
            "bundle_id": str(bundle.id),
            "withdrawal_waiver_accepted_at": consent_timestamp.isoformat(),
        }
    )
    
    audit_logger.info(
        f"STRIPE BUNDLE CHECKOUT CREATED: User {request.user.username} (ID: {request.user.id}) created Stripe checkout session for Bundle {bundle.name} (ID: {bundle.id}). Session ID: {checkout_session.id}"
    )
    
    return redirect(checkout_session.url, code=303)

@login_required
def payment_success(request):
    """Vue de confirmation visuelle après paiement."""
    return render(request, 'payments/success.html', {'title': "Paiement Réussi"})

@login_required
def payment_cancel(request):
    """Vue d'annulation du paiement."""
    return render(request, 'payments/cancel.html', {'title': "Paiement Annulé"})

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
        module_id = session.metadata.get("module_id") if session.metadata else None
        bundle_id = session.metadata.get("bundle_id") if session.metadata else None
        waiver_ts = session.metadata.get("withdrawal_waiver_accepted_at") if session.metadata else None

        # Backup via client_reference_id si besoin
        if not user_id and hasattr(session, 'client_reference_id'):
            user_id = session.client_reference_id

        print(f"WEBHOOK : User={user_id}, Module={module_id}, Bundle={bundle_id}")

        if not user_id:
            print("WEBHOOK ERROR : Identifiant Utilisateur manquant")
            return HttpResponse(status=200)

        if not module_id and not bundle_id:
            print("WEBHOOK ERROR : Identifiants Module et Bundle manquants")
            return HttpResponse(status=200)

        # Logique de création en base de données
        try:
            user = User.objects.get(id=user_id)
            amount_total = getattr(session, 'amount_total', 0)
            
            # Récupération du timestamp capturé avant paiement
            consent_dt = timezone.datetime.fromisoformat(waiver_ts) if waiver_ts else timezone.now()
            if timezone.is_naive(consent_dt):
                consent_dt = timezone.make_aware(consent_dt)

            order = Order.objects.create(
                user=user,
                status='pending',
                total_amount=amount_total / 100,
                withdrawal_waiver_accepted_at=consent_dt,
                stripe_payment_intent_id=getattr(session, 'payment_intent', None)
            )
            
            if module_id:
                module = Module.objects.get(id=module_id)
                OrderItem.objects.create(
                    order=order,
                    module=module,
                    price_at_purchase=module.price
                )
                order.status = 'completed'
                order.full_clean()
                order.save()
                License.objects.create(
                    user=user,
                    module=module,
                    is_active=True,
                    max_activations=1
                )
                print(f"SUCCESS : Achat et Licence enregistrés pour le module {module.name} ({user.username})")
                audit_logger.info(
                    f"STRIPE WEBHOOK MODULE PURCHASE SUCCESS: User {user.username} (ID: {user.id}) successfully purchased Module {module.name} (ID: {module.id}) via Stripe. Order ID: {order.id}. PaymentIntent: {order.stripe_payment_intent_id}."
                )
                
            elif bundle_id:
                bundle = ModuleBundle.objects.get(id=bundle_id)
                OrderItem.objects.create(
                    order=order,
                    bundle=bundle,
                    price_at_purchase=bundle.final_price
                )
                order.status = 'completed'
                order.full_clean()
                order.save()
                # Créer une licence pour CHAQUE module inclus dans le pack
                for module in bundle.modules.all():
                    License.objects.create(
                        user=user,
                        module=module,
                        is_active=True,
                        max_activations=1
                    )
                print(f"SUCCESS : Achat du pack {bundle.name} et licences de tous ses modules enregistrées pour {user.username}")
                audit_logger.info(
                    f"STRIPE WEBHOOK BUNDLE PURCHASE SUCCESS: User {user.username} (ID: {user.id}) successfully purchased Bundle {bundle.name} (ID: {bundle.id}) via Stripe. Order ID: {order.id}. PaymentIntent: {order.stripe_payment_intent_id}. Licenses generated for {[m.name for m in bundle.modules.all()]}."
                )
            
        except (User.DoesNotExist, Module.DoesNotExist, ModuleBundle.DoesNotExist) as e:
            print(f"WEBHOOK ERROR : Entité introuvable ({str(e)})")
            audit_logger.error(f"STRIPE WEBHOOK DATABASE CREATION FAILED: Entity not found. Error: {str(e)}")

    return HttpResponse(status=200)

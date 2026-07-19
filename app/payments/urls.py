"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Gestion du routage d'URL pour les paiements Stripe.
              Définit les routes de checkout et de succès.
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:module_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('checkout-bundle/<int:bundle_id>/', views.create_bundle_checkout_session, name='create_bundle_checkout_session'),
    path('success/', views.payment_success, name='payment_success'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
]

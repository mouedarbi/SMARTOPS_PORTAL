"""
Fichier : tests_audit_log.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Journalisation des achats refusés ou en échec (logger « audit »).
"""

from decimal import Decimal
from unittest.mock import patch

import stripe
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from catalog.models import Category, Module
from payments.models import Order

User = get_user_model()
CONSENTS = {'withdrawal_waiver': 'on', 'core_tested_ack': 'on'}


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], SECURE_SSL_REDIRECT=False)
class PaymentAuditLogTests(TestCase):

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        self.user = User.objects.create_user('acheteur', 'acheteur@example.org', 'x', is_client=True)
        category = Category.objects.create(name='IoT', slug='iot-audit')
        self.module = Module.objects.create(name='Module Audit', slug='module-audit', category=category,
                                            short_description='Court', price=Decimal('99.00'), is_active=True)
        self.client.force_login(self.user)
        self.url = reverse('payments:create_checkout_session', kwargs={'module_id': self.module.id})

    def output_of(self, action, level='INFO'):
        with self.assertLogs('audit', level=level) as captured:
            action()
        return '\n'.join(captured.output)

    def test_purchase_refused_without_consents(self):
        output = self.output_of(lambda: self.client.post(self.url, {}))
        self.assertIn(f'PURCHASE REFUSED: User acheteur (ID: {self.user.id}) did not accept the required consents '
                      f'for Module Module Audit (ID: {self.module.id})', output)

    @override_settings(STRIPE_SECRET_KEY='sk_test_audit')
    @patch('payments.views.stripe.checkout.Session.create', side_effect=stripe.StripeError('Stripe injoignable'))
    def test_stripe_checkout_failure_is_logged_and_handled(self, _create):
        with self.assertLogs('audit', level='INFO') as captured:
            response = self.client.post(self.url, CONSENTS)
        self.assertRedirects(response, reverse('catalog:module_detail', kwargs={'slug': self.module.slug}),
                             fetch_redirect_response=False)
        self.assertIn('STRIPE CHECKOUT FAILED: User acheteur', '\n'.join(captured.output))
        self.assertIn('Stripe injoignable', '\n'.join(captured.output))
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def post_webhook(self):
        return self.client.post(reverse('payments:stripe_webhook'), data=b'{}', content_type='application/json',
                                HTTP_STRIPE_SIGNATURE='sig')

    def test_webhook_with_invalid_signature_is_logged(self):
        output = self.output_of(self.post_webhook)
        self.assertIn('STRIPE WEBHOOK REJECTED', output)

    @patch('stripe.Webhook.construct_event')
    def test_failed_payment_event_is_logged(self, construct_event):
        construct_event.return_value = {
            'type': 'payment_intent.payment_failed',
            'data': {'object': {'id': 'pi_refuse', 'metadata': {'user_id': str(self.user.id), 'module_id': str(self.module.id)}}},
        }
        with self.assertLogs('audit', level='INFO') as captured:
            response = self.post_webhook()
        self.assertEqual(response.status_code, 200)
        output = '\n'.join(captured.output)
        self.assertIn('STRIPE PAYMENT FAILED: Event payment_intent.payment_failed for pi_refuse', output)
        self.assertIn(f'User ID: {self.user.id}', output)
        self.assertFalse(Order.objects.exists())

    @patch('stripe.Webhook.construct_event')
    def test_webhook_without_user_is_logged(self, construct_event):
        construct_event.return_value = {
            'type': 'checkout.session.completed',
            'data': {'object': stripe.checkout.Session.construct_from(
                {'id': 'cs_sans_user', 'metadata': {}, 'client_reference_id': None}, 'sk_test')},
        }
        output = self.output_of(self.post_webhook)
        self.assertIn('STRIPE WEBHOOK FAILED: Missing user identifier in checkout session cs_sans_user', output)

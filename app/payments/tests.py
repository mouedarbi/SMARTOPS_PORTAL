"""
Fichier : tests.py
Application : payments
Auteur : Mohamed Ouedarbi
Description : Tests unitaires du parcours de paiement, simulation démo, webhook Stripe et consentement de rétractation.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, Client as HttpClient, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from catalog.models import Category, Module
from payments.models import Order, OrderItem
from licensing.models import License

User = get_user_model()


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    STRIPE_SECRET_KEY="",
    STRIPE_WEBHOOK_SECRET="whsec_test_secret"
)
class PaymentWorkflowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='client_buyer',
            email='buyer@smartops.org',
            password='Password123!'
        )
        self.category = Category.objects.create(name='IoT & Capteurs', slug='iot')
        self.module = Module.objects.create(
            name='Module Capteur Température',
            slug='module-capteur-temp',
            category=self.category,
            short_description='Intégration capteurs IoT.',
            price=Decimal('150.00'),
            is_active=True
        )
        self.client_http = HttpClient()
        self.client_http.login(username='client_buyer', password='Password123!')

    def test_mock_checkout_module_generates_order_license_and_waiver(self):
        """Vérifie que le mode simulation crée bien la commande, le consentement de rétractation et la licence."""
        url = reverse('payments:create_checkout_session', kwargs={'module_id': self.module.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('payments:payment_success'))

        # Vérification Order
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'completed')
        self.assertEqual(order.total_amount, Decimal('150.00'))
        self.assertIsNotNone(order.withdrawal_waiver_accepted_at)

        # Vérification OrderItem
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.module, self.module)

        # Vérification License
        license_obj = License.objects.filter(user=self.user, module=self.module).first()
        self.assertIsNotNone(license_obj)
        self.assertTrue(license_obj.is_active)

    def test_stripe_webhook_invalid_signature(self):
        """Vérifie le rejet (HTTP 400) d'un webhook Stripe avec signature incorrecte."""
        url = reverse('payments:stripe_webhook')
        response = self.client_http.post(
            url,
            data=b'{"id": "evt_test"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_sig'
        )
        self.assertEqual(response.status_code, 400)

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_successful_checkout(self, mock_construct_event):
        """Vérifie le traitement réussi d'un événement checkout.session.completed."""
        fake_session = MagicMock()
        fake_session.client_reference_id = str(self.user.id)
        fake_session.amount_total = 15000  # 150.00 EUR en centimes
        fake_session.payment_intent = 'pi_test_123456789'
        fake_session.metadata = {
            'user_id': str(self.user.id),
            'module_id': str(self.module.id),
            'bundle_id': None
        }

        mock_construct_event.return_value = {
            'type': 'checkout.session.completed',
            'data': {
                'object': fake_session
            }
        }

        url = reverse('payments:stripe_webhook')
        response = self.client_http.post(
            url,
            data=b'{"id": "evt_mock"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )
        self.assertEqual(response.status_code, 200)

        # Vérification Order et License créés via webhook
        order = Order.objects.filter(stripe_payment_intent_id='pi_test_123456789').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'completed')
        self.assertIsNotNone(order.withdrawal_waiver_accepted_at)

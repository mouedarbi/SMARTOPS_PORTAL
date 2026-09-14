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
from licensing.models import License, SupportSubscription

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
        response = self.client_http.post(url, data={'withdrawal_waiver': 'on'})
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
        """Vérifie le traitement réussi d'un webhook Stripe avec réconciliation exacte du consentement préalable."""
        fake_session = MagicMock()
        fake_session.client_reference_id = str(self.user.id)
        fake_session.amount_total = 15000  # 150.00 EUR en centimes
        fake_session.payment_intent = 'pi_test_123456789'
        prior_waiver_ts = '2026-08-19T09:30:00+00:00'
        fake_session.metadata = {
            'user_id': str(self.user.id),
            'module_id': str(self.module.id),
            'bundle_id': None,
            'withdrawal_waiver_accepted_at': prior_waiver_ts
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
        self.assertEqual(order.withdrawal_waiver_accepted_at.isoformat(), prior_waiver_ts)

    def test_order_full_clean_rejects_empty_order_without_items(self):
        """F4 : Vérifie que full_clean() lève une ValidationError si une commande completed n'a aucun OrderItem."""
        from django.core.exceptions import ValidationError
        order = Order.objects.create(
            user=self.user,
            status='completed',
            total_amount=Decimal('150.00'),
            withdrawal_waiver_accepted_at=timezone.now()
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    @patch('stripe.checkout.Session.create')
    def test_stripe_session_creation_passes_waiver_in_metadata(self, mock_session_create):
        """F4 : Vérifie que la création d'une session Stripe capture l'horodatage et le transmet dans metadata."""
        mock_session_create.return_value = MagicMock(url='https://checkout.stripe.com/pay/test', id='cs_test_123')
        
        with override_settings(STRIPE_SECRET_KEY="sk_test_mock_key"):
            url = reverse('payments:create_checkout_session', kwargs={'module_id': self.module.id})
            before_call = timezone.now()
            response = self.client_http.post(url, data={'withdrawal_waiver': 'on'})
            after_call = timezone.now()

            self.assertEqual(response.status_code, 302)
            self.assertTrue(mock_session_create.called)
            call_kwargs = mock_session_create.call_args.kwargs
            self.assertIn('metadata', call_kwargs)
            metadata = call_kwargs['metadata']
            self.assertIn('withdrawal_waiver_accepted_at', metadata)
            
            # Vérification chronologique : le consentement est capturé pendant l'appel
            waiver_dt = timezone.datetime.fromisoformat(metadata['withdrawal_waiver_accepted_at'])
            self.assertTrue(before_call <= waiver_dt <= after_call)

    @patch('stripe.checkout.Session.create')
    def test_checkout_rejected_without_waiver_consent(self, mock_session_create):
        """F4 : Une requête sans la case de renonciation cochée doit être bloquée avant tout appel à Stripe."""
        with override_settings(STRIPE_SECRET_KEY="sk_test_mock_key"):
            url = reverse('payments:create_checkout_session', kwargs={'module_id': self.module.id})
            response = self.client_http.post(url, data={})

            self.assertEqual(response.status_code, 302)
            self.assertRedirects(
                response,
                reverse('catalog:module_detail', kwargs={'slug': self.module.slug})
            )

            # Aucun appel Stripe, aucune commande, aucune licence ne doivent être créés
            self.assertFalse(mock_session_create.called)
            self.assertFalse(Order.objects.filter(user=self.user).exists())
            self.assertFalse(License.objects.filter(user=self.user, module=self.module).exists())


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    STRIPE_SECRET_KEY="",
    STRIPE_WEBHOOK_SECRET="whsec_test_secret"
)
class SupportSubscriptionWorkflowTestCase(TestCase):
    """Tests du parcours d'abonnement support annuel (paiement unique, expiration +365j)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='support_buyer',
            email='support_buyer@smartops.org',
            password='Password123!'
        )
        self.category = Category.objects.create(name='IoT & Capteurs', slug='iot-support')
        self.module = Module.objects.create(
            name='Module Avec Support',
            slug='module-avec-support',
            category=self.category,
            short_description='Module proposant un support annuel.',
            price=Decimal('150.00'),
            support_annual_price=Decimal('49.00'),
            is_active=True
        )
        self.module_no_support = Module.objects.create(
            name='Module Sans Support',
            slug='module-sans-support',
            category=self.category,
            short_description='Module ne proposant pas de support.',
            price=Decimal('19.00'),
            is_active=True
        )
        self.client_http = HttpClient()
        self.client_http.login(username='support_buyer', password='Password123!')

    def test_support_checkout_blocked_when_not_configured(self):
        """Un module sans support_annual_price refuse la souscription."""
        License.objects.create(user=self.user, module=self.module_no_support, is_active=True, max_activations=1)
        url = reverse('payments:create_support_checkout_session', kwargs={'module_id': self.module_no_support.id})
        response = self.client_http.post(url)
        self.assertRedirects(response, reverse('users:dashboard'))
        self.assertFalse(SupportSubscription.objects.exists())
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_support_checkout_blocked_without_owned_license(self):
        """Impossible de souscrire au support d'un module que l'on ne possède pas."""
        url = reverse('payments:create_support_checkout_session', kwargs={'module_id': self.module.id})
        response = self.client_http.post(url)
        self.assertRedirects(response, reverse('users:dashboard'))
        self.assertFalse(SupportSubscription.objects.exists())
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_mock_support_checkout_creates_subscription_without_license(self):
        """Mode démo : la souscription support crée Order + OrderItem(support) + SupportSubscription, sans License."""
        License.objects.create(user=self.user, module=self.module, is_active=True, max_activations=1)
        url = reverse('payments:create_support_checkout_session', kwargs={'module_id': self.module.id})
        response = self.client_http.post(url)
        self.assertRedirects(response, reverse('payments:payment_success'))

        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'completed')
        self.assertEqual(order.total_amount, Decimal('49.00'))

        item = order.items.first()
        self.assertEqual(item.product_type, 'support')
        self.assertEqual(item.price_at_purchase, Decimal('49.00'))

        # Une seule License existante (celle créée manuellement) : la souscription support n'en crée pas.
        self.assertEqual(License.objects.filter(user=self.user, module=self.module).count(), 1)

        sub = SupportSubscription.objects.get(user=self.user, module=self.module)
        self.assertTrue(sub.is_valid)
        expected_expiry = timezone.now() + timezone.timedelta(days=365)
        self.assertAlmostEqual(sub.expires_at, expected_expiry, delta=timezone.timedelta(minutes=1))

    def test_mock_support_checkout_renewal_extends_expiry(self):
        """Un second achat prolonge l'abonnement existant plutôt que d'en créer un nouveau."""
        License.objects.create(user=self.user, module=self.module, is_active=True, max_activations=1)
        url = reverse('payments:create_support_checkout_session', kwargs={'module_id': self.module.id})

        self.client_http.post(url)
        first_sub = SupportSubscription.objects.get(user=self.user, module=self.module)
        first_expiry = first_sub.expires_at

        self.client_http.post(url)
        self.assertEqual(SupportSubscription.objects.filter(user=self.user, module=self.module).count(), 1)
        second_sub = SupportSubscription.objects.get(user=self.user, module=self.module)
        self.assertEqual(second_sub.expires_at, first_expiry + timezone.timedelta(days=365))
        self.assertEqual(Order.objects.filter(user=self.user).count(), 2)

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_support_subscription(self, mock_construct_event):
        """Le webhook Stripe crée/renouvelle une SupportSubscription quand product_type='support_subscription'."""
        License.objects.create(user=self.user, module=self.module, is_active=True, max_activations=1)

        fake_session = MagicMock()
        fake_session.client_reference_id = str(self.user.id)
        fake_session.amount_total = 4900  # 49.00 EUR en centimes
        fake_session.payment_intent = 'pi_test_support_123'
        fake_session.metadata = {
            'user_id': str(self.user.id),
            'module_id': str(self.module.id),
            'bundle_id': None,
            'product_type': 'support_subscription',
        }
        mock_construct_event.return_value = {
            'type': 'checkout.session.completed',
            'data': {'object': fake_session}
        }

        url = reverse('payments:stripe_webhook')
        response = self.client_http.post(
            url,
            data=b'{"id": "evt_mock_support"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )
        self.assertEqual(response.status_code, 200)

        order = Order.objects.filter(stripe_payment_intent_id='pi_test_support_123').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'completed')
        self.assertEqual(order.items.first().product_type, 'support')

        sub = SupportSubscription.objects.get(user=self.user, module=self.module)
        self.assertTrue(sub.is_valid)
        # Le webhook ne doit pas créer de License supplémentaire (celle possédée reste unique).
        self.assertEqual(License.objects.filter(user=self.user, module=self.module).count(), 1)


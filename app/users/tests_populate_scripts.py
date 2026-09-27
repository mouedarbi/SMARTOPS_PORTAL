"""
Fichier : tests_populate_scripts.py
Projet : Marketplace SMARTOPS
Application : users
Description : Les scripts de données de démonstration refusent de s'exécuter hors développement.
"""

import os
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from payments.models import Order
from payments import populate_purchases
from users import populate_portal_clients

User = get_user_model()


class PopulateScriptsGuardTests(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user('client_reel', 'reel@example.org', 'x', is_client=True)
        self.order = Order.objects.create(user=self.customer, status='completed', total_amount=Decimal('59.96'))

    @override_settings(DEBUG=False)
    def test_client_script_refuses_to_run_in_production(self):
        with self.assertRaises(SystemExit):
            populate_portal_clients.run()
        self.assertTrue(User.objects.filter(pk=self.customer.pk).exists())

    @override_settings(DEBUG=False)
    def test_purchase_script_refuses_to_run_in_production(self):
        with self.assertRaises(SystemExit):
            populate_purchases.run()
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    @override_settings(DEBUG=True)
    def test_admin_password_is_required_from_environment(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('PORTAL_ADMIN_PASSWORD', None)
            with self.assertRaises(SystemExit):
                populate_portal_clients.run()
        self.assertFalse(User.objects.filter(username='admin').exists())

    def test_no_hardcoded_admin_password(self):
        with open(populate_portal_clients.__file__, encoding='utf-8') as source:
            self.assertNotIn('adminpassword123', source.read())

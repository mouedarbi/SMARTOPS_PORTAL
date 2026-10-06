"""
Fichier : tests_account_retention.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Un compte client lié à des commandes ou licences n'est jamais supprimé physiquement :
              il est anonymisé, commandes et licences conservées (§9.5 du rapport, Art. 17.3.b RGPD).
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Category, Module
from licensing.models import License
from payments.models import Order

User = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountRetentionTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('root', 'root@example.org', 'x')
        self.customer = User.objects.create_user('client1', 'client1@example.org', 'x', is_client=True)
        cat = Category.objects.create(name='Sécurité', slug='securite-ret')
        module = Module.objects.create(name='Module Badgeuse', slug='module-badgeuse-ret',
                                       price=Decimal('99.00'), category=cat, is_active=True)
        self.license = License.objects.create(user=self.customer, module=module, is_active=True, max_activations=1)
        self.order = Order.objects.create(user=self.customer, status='completed', total_amount=Decimal('99.00'))
        self.client.force_login(self.admin)

    def test_physical_deletion_is_refused_by_the_database_layer(self):
        with self.assertRaises(ProtectedError):
            self.customer.delete()
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_django_admin_does_not_offer_deletion_for_a_customer_with_orders(self):
        url = reverse('admin:users_user_delete', args=[self.customer.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'post': 'yes'}).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.customer.pk).exists())

    def test_django_admin_bulk_delete_keeps_the_customer(self):
        self.client.post(reverse('admin:users_user_changelist'),
                         {'action': 'delete_selected', '_selected_action': [self.customer.pk], 'post': 'yes'})
        self.assertTrue(User.objects.filter(pk=self.customer.pk).exists())
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_admin_anonymize_action_keeps_orders_and_licenses(self):
        response = self.client.post(reverse('admin:users_user_changelist'),
                                    {'action': 'anonymize_accounts', '_selected_action': [self.customer.pk]})
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_deleted)
        self.assertFalse(self.customer.is_active)
        self.assertTrue(self.customer.email.endswith('@supprime.invalid'))
        self.order.refresh_from_db()
        self.license.refresh_from_db()
        self.assertEqual(self.order.user_id, self.customer.pk)
        self.assertEqual(self.license.user_id, self.customer.pk)

    def test_anonymize_action_never_touches_superusers(self):
        self.client.post(reverse('admin:users_user_changelist'),
                         {'action': 'anonymize_accounts', '_selected_action': [self.admin.pk]})
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_deleted)

    def test_account_without_purchases_can_still_be_deleted(self):
        visitor = User.objects.create_user('visiteur', 'v@example.org', 'x')
        url = reverse('admin:users_user_delete', args=[visitor.pk])
        self.client.post(url, {'post': 'yes'})
        self.assertFalse(User.objects.filter(pk=visitor.pk).exists())

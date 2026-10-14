"""
Fichier : tests_admin.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Garde-fous de l'admin Django : licences et installations ne se suppriment pas.
"""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Module
from licensing.models import Installation, License

User = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AdminDeletionTestCase(TestCase):
    def setUp(self):
        admin = User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client.force_login(admin)
        buyer = User.objects.create_user('buyer', 'buyer@example.org', 'x')
        module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('99.00'),
                                       short_description='x', description='x')
        self.installation = Installation.objects.create(installation_uuid=uuid.uuid4(), user=buyer)
        self.license = License.objects.create(user=buyer, module=module, installation=self.installation,
                                              activation_count=1)

    def test_license_cannot_be_deleted_in_django_admin(self):
        url = reverse('admin:licensing_license_delete', args=[self.license.pk])
        self.assertEqual(self.client.post(url, {'post': 'yes'}).status_code, 403)
        self.client.post(reverse('admin:licensing_license_changelist'),
                         {'action': 'delete_selected', '_selected_action': [self.license.pk], 'post': 'yes'})
        self.assertTrue(License.objects.filter(pk=self.license.pk).exists())

    def test_license_can_still_be_deactivated_in_django_admin(self):
        response = self.client.get(reverse('admin:licensing_license_change', args=[self.license.pk]))
        self.assertContains(response, 'name="is_active"')

"""
Fichier : tests_deletions.py
Projet : Marketplace SMARTOPS
Application : backoffice
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Garde-fous des suppressions du backoffice : ce qu'un client a acheté n'est jamais effacé.
"""

import datetime
import json
import os
import tempfile
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db.models import ProtectedError
from django.test import TestCase, Client as HttpClient, override_settings
from django.urls import reverse
from django.utils import translation

from catalog.models import Category, CoreVersion, Module, ModuleVersion
from licensing.models import License
from payments.models import Order, OrderItem

User = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DeletionTestCase(TestCase):
    """Administrateur connecté, une catégorie, une version du Core et un module avec une version."""

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        self.category = Category.objects.create(name='Analytics', slug='analytics')
        self.core = CoreVersion.objects.create(version='1.0.0')
        self.module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('99.00'),
                                            category=self.category, short_description='x', description='x')
        self.version = ModuleVersion.objects.create(module=self.module, version_number='1.0.0',
                                                    release_date=datetime.date(2026, 1, 1),
                                                    min_core_version=self.core, file='modules/packages/bi.tar.gz')

    def _messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]


class ProtectedDeleteTestCase(DeletionTestCase):
    """Une suppression bloquée par une référence affiche un message au lieu d'une erreur 500 (#69)."""

    def test_core_version_in_use_is_kept_with_a_message(self):
        response = self.client_http.post(reverse('backoffice:core_version_delete', kwargs={'pk': self.core.pk}))
        self.assertRedirects(response, reverse('backoffice:core_version_edit', kwargs={'pk': self.core.pk}))
        self.assertTrue(CoreVersion.objects.filter(pk=self.core.pk).exists())
        self.assertIn("La version Core 1.0.0 est requise par 1 version(s) de module : "
                      "marquez-la plutôt comme non supportée.", self._messages(response))

    def test_message_is_translated(self):
        expected = {'en': 'Core version 1.0.0 is required by 1 module version(s)',
                    'nl': 'Core-versie 1.0.0 is vereist door 1 moduleversie(s)'}
        for lang, text in expected.items():
            with translation.override(lang):
                url = reverse('backoffice:core_version_delete', kwargs={'pk': self.core.pk})
            response = self.client_http.post(url)
            self.assertTrue(any(text in m for m in self._messages(response)), lang)

    def test_unused_core_version_is_deleted(self):
        unused = CoreVersion.objects.create(version='2.0.0')
        self.client_http.post(reverse('backoffice:core_version_delete', kwargs={'pk': unused.pk}))
        self.assertFalse(CoreVersion.objects.filter(pk=unused.pk).exists())


class SoldModuleDeleteTestCase(DeletionTestCase):
    """Un module vendu est retiré de la vente, jamais supprimé : la licence reste utilisable (#70)."""

    def setUp(self):
        super().setUp()
        self.buyer = User.objects.create_user('buyer', 'buyer@example.org', 'Password123!')
        order = Order.objects.create(user=self.buyer, status='completed', total_amount=Decimal('99.00'))
        OrderItem.objects.create(order=order, module=self.module, price_at_purchase=Decimal('99.00'))
        self.license = License.objects.create(user=self.buyer, module=self.module)
        self.url = reverse('backoffice:module_delete', kwargs={'pk': self.module.pk})

    def test_confirmation_page_announces_withdrawal(self):
        response = self.client_http.get(self.url)
        self.assertContains(response, 'Retirer le module de la vente')
        self.assertContains(response, '(1 licence(s))')
        self.assertContains(response, 'Oui, retirer de la vente')

    def test_sold_module_is_withdrawn_not_deleted(self):
        self.client_http.post(self.url)
        self.module.refresh_from_db()
        self.assertFalse(self.module.is_active)
        self.assertTrue(License.objects.filter(pk=self.license.pk).exists())
        self.assertTrue(ModuleVersion.objects.filter(pk=self.version.pk).exists())
        self.assertEqual(OrderItem.objects.get().module, self.module)
        self.assertEqual(self.client_http.get(reverse('catalog:module_list')).status_code, 200)
        self.assertNotContains(self.client_http.get(reverse('catalog:module_list')), 'Module BI')

    def test_unused_license_still_activates_and_downloads_after_withdrawal(self):
        self.client_http.post(self.url)
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            os.makedirs(os.path.join(media, 'modules/packages'))
            with open(os.path.join(media, 'modules/packages/bi.tar.gz'), 'wb') as package:
                package.write(b'paquet')
            response = self.client.post('/api/licensing/validate/', json.dumps({
                'license_key': str(self.license.license_key), 'installation_uuid': str(uuid.uuid4()),
            }), content_type='application/json')
            self.assertEqual(response.status_code, 200, response.content)
            download = self.client.get(reverse('download_module_package', kwargs={'license_key': self.license.license_key}))
            self.assertEqual(download.status_code, 200)
            self.assertEqual(b''.join(download.streaming_content), b'paquet')

    def test_sold_module_cannot_be_deleted_outside_the_backoffice(self):
        with self.assertRaises(ProtectedError):
            self.module.delete()

    def test_module_never_sold_is_deleted(self):
        draft = Module.objects.create(name='Brouillon', slug='brouillon', price=Decimal('10.00'),
                                      short_description='x', description='x')
        self.assertContains(self.client_http.get(reverse('backoffice:module_delete', kwargs={'pk': draft.pk})),
                            "Ce module n'a jamais été vendu.")
        self.client_http.post(reverse('backoffice:module_delete', kwargs={'pk': draft.pk}))
        self.assertFalse(Module.objects.filter(pk=draft.pk).exists())

    def test_confirmation_page_is_translated(self):
        for lang, text in (('en', 'Withdraw the module from sale'), ('nl', 'Module uit de verkoop halen')):
            with translation.override(lang):
                url = reverse('backoffice:module_delete', kwargs={'pk': self.module.pk})
            self.assertContains(self.client_http.get(url), text)

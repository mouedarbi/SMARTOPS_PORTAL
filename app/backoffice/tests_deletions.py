"""
Fichier : tests_deletions.py
Projet : Marketplace SMARTOPS
Application : backoffice
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Garde-fous des suppressions du backoffice : ce qu'un client a acheté n'est jamais effacé.
"""

import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, Client as HttpClient, override_settings
from django.urls import reverse
from django.utils import translation

from catalog.models import Category, CoreVersion, Module, ModuleVersion

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

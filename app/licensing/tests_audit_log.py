"""
Fichier : tests_audit_log.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Journalisation des appels de l'API de licences (validation, téléchargement, enregistrement, synchronisation).
"""

import uuid
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Category, Module
from licensing.models import Installation, License

User = get_user_model()


class LicensingAuditLogTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('licencie', 'licencie@example.org', 'x', is_client=True)
        category = Category.objects.create(name='Sécurité', slug='securite-audit')
        self.module = Module.objects.create(name='Module Journal', slug='module-journal', category=category,
                                            price=Decimal('50.00'), is_active=True)
        self.license = License.objects.create(user=self.user, module=self.module, is_active=True, max_activations=1)
        self.key = str(self.license.license_key)

    def post(self, url, data):
        with self.assertLogs('audit', level='INFO') as captured:
            response = self.client.post(url, data=data, content_type='application/json')
        return response, '\n'.join(captured.output)

    def test_license_bound_to_another_installation(self):
        self.license.installation = Installation.objects.create(installation_uuid=uuid.uuid4(), user=self.user)
        self.license.save()
        response, output = self.post('/api/licensing/validate/',
                                     {'license_key': self.key, 'installation_uuid': str(uuid.uuid4())})
        self.assertEqual(response.status_code, 403)
        self.assertIn(f'API LICENSE VALIDATION FAILED: Key {self.key} is already bound to installation', output)

    def test_module_without_package(self):
        response, output = self.post('/api/licensing/validate/',
                                     {'license_key': self.key, 'installation_uuid': str(uuid.uuid4())})
        self.assertEqual(response.status_code, 404)
        self.assertIn('API LICENSE VALIDATION FAILED: No package version available for module Module Journal', output)

    def test_unexpected_validation_error_is_logged_with_traceback(self):
        with patch('licensing.models.Installation.objects.get_or_create', side_effect=RuntimeError('panne')):
            response, output = self.post('/api/licensing/validate/',
                                         {'license_key': self.key, 'installation_uuid': str(uuid.uuid4())})
        self.assertEqual(response.status_code, 500)
        self.assertIn('API LICENSE VALIDATION ERROR', output)
        self.assertIn('RuntimeError: panne', output)

    def test_sync_success_and_missing_uuid(self):
        installation_uuid = str(uuid.uuid4())
        response, output = self.post('/api/licensing/register/', {'installation_uuid': installation_uuid})
        self.assertEqual(response.status_code, 201)
        self.assertIn(f'API REGISTER SUCCESS: Installation {installation_uuid} registered', output)
        secret = response.json()['installation_secret']
        with self.assertLogs('audit', level='INFO') as captured:
            response = self.client.post('/api/licensing/sync/', data={
                'installation_uuid': installation_uuid, 'company_name': 'ACME', 'core_version': '1.0.0',
                'installed_modules': [{'slug': 'module-journal', 'version': '1.0.0'}]},
                content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {secret}')
        output = '\n'.join(captured.output)
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'API SYNC SUCCESS: Installation {installation_uuid} (ACME, Core 1.0.0) synchronized with 1 module(s)', output)
        response, output = self.post('/api/licensing/sync/', {'company_name': 'ACME'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('API SYNC FAILED: Missing installation UUID', output)

    def test_sync_unexpected_error(self):
        with patch('licensing.models.Installation.objects.filter', side_effect=RuntimeError('panne')):
            response, output = self.post('/api/licensing/sync/', {'installation_uuid': str(uuid.uuid4())})
        self.assertEqual(response.status_code, 500)
        self.assertIn('API SYNC ERROR', output)
        self.assertNotIn('panne', response.json()['error'])

    def test_download_failures(self):
        with self.assertLogs('audit', level='INFO') as captured:
            self.assertEqual(self.client.get(f'/api/licensing/download/{uuid.uuid4()}/').status_code, 404)
            self.assertEqual(self.client.get(f'/api/licensing/download/{self.key}/').status_code, 404)
        output = '\n'.join(captured.output)
        self.assertIn('API PACKAGE DOWNLOAD FAILED: License', output)
        self.assertIn('API PACKAGE DOWNLOAD FAILED: No package file for module Module Journal', output)

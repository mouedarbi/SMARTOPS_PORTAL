"""
Fichier : tests.py
Application : downloads
Auteur : Mohamed Ouedarbi
Description : Tests unitaires pour le téléchargement sécurisé des modules et la télémétrie des instances.
"""

import uuid
import datetime
from django.test import TestCase, Client as HttpClient, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from catalog.models import Category, Module, CoreVersion, ModuleVersion
from licensing.models import License, Installation

User = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SecureDownloadAndSyncTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='dl_client',
            email='dl@client.com',
            password='password123'
        )
        self.category = Category.objects.create(name='Mobile', slug='mobile')
        self.module = Module.objects.create(
            name='Module Scanner QR',
            slug_fr='module-scanner-qr',
            price=49.00,
            category=self.category,
            is_active=True
        )
        self.core_version = CoreVersion.objects.create(version='1.0.0')

        # Création d'un fichier package fictif
        dummy_file = SimpleUploadedFile("package.tar.gz", b"fake tarball archive content", content_type="application/gzip")
        self.module_version = ModuleVersion.objects.create(
            module=self.module,
            version_number='1.0.0',
            release_date=datetime.date.today(),
            min_core_version=self.core_version,
            file=dummy_file
        )

        self.license = License.objects.create(
            user=self.user,
            module=self.module,
            is_active=True,
            max_activations=1
        )
        self.client_http = HttpClient()

    def test_download_package_with_valid_active_license(self):
        """Vérifie le téléchargement réussi du package avec une licence valide."""
        url = reverse('download_module_package', kwargs={'license_key': str(self.license.license_key)})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.get('Content-Disposition', ''))
        self.assertIn('.tar.gz', response.get('Content-Disposition', ''))

    def test_download_package_with_invalid_license_returns_404(self):
        """Vérifie le rejet 404 en cas de tentative de téléchargement avec une fausse clé."""
        random_key = str(uuid.uuid4())
        url = reverse('download_module_package', kwargs={'license_key': random_key})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 404)

    def test_sync_installation_telemetry_api(self):
        """Vérifie l'enregistrement et la mise à jour de la télémétrie d'une installation Core."""
        inst_uuid = str(uuid.uuid4())
        response = self.client_http.post(
            '/api/licensing/sync/',
            data={
                'installation_uuid': inst_uuid,
                'company_name': 'Industrie ACME Sprl',
                'core_version': '1.0.0',
                'installed_modules': [{'slug': self.module.slug_fr, 'version': '1.0.0'}]
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))

        # Vérification en base
        installation = Installation.objects.filter(installation_uuid=inst_uuid).first()
        self.assertIsNotNone(installation)
        self.assertEqual(installation.company_name, 'Industrie ACME Sprl')

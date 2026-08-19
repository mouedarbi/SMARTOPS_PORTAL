from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import IntegrityError
from catalog.models import Module, Category
from licensing.models import License, Installation
import uuid

User = get_user_model()

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LicenseWorkflowTestCase(TestCase):
    """
    Tests d'intégration et unitaires pour valider les contraintes du TFE :
    1. Achat de multiples produits identiques générant des clés distinctes.
    2. Regroupement par module dans l'espace client (dashboard).
    3. Masquage et disparition automatique des clés activées/utilisées de l'écran.
    """
    
    def setUp(self):
        # 1. Création d'un utilisateur client
        self.user = User.objects.create_user(
            username='testclient',
            email='test@client.com',
            password='testpassword123',
            is_client=True
        )
        
        # 2. Création d'une catégorie et d'un module
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.module = Module.objects.create(
            name='Signature Électronique',
            slug_fr='signature-electronique',
            price=79.00,
            category=self.category,
            is_active=True
        )
        
        # 3. Initialisation du client HTTP Django de test
        self.client = Client()
        self.client.login(username='testclient', password='testpassword123')

    def test_multiple_identical_module_purchases_generates_multiple_licenses(self):
        """
        Vérifie que l'achat multiple d'un même produit génère bien
        plusieurs clés de licences distinctes en base de données pour l'utilisateur.
        """
        # Achat du module (Licence 1)
        lic1 = License.objects.create(
            user=self.user,
            module=self.module,
            is_active=True,
            max_activations=1
        )
        
        # Nouvel achat du même module (Licence 2)
        lic2 = License.objects.create(
            user=self.user,
            module=self.module,
            is_active=True,
            max_activations=1
        )
        
        # Vérification de l'existence de 2 licences distinctes
        user_licenses = License.objects.filter(user=self.user, module=self.module)
        self.assertEqual(user_licenses.count(), 2)
        self.assertNotEqual(lic1.license_key, lic2.license_key)
        self.assertTrue(lic1.is_active)
        self.assertTrue(lic2.is_active)

    def test_dashboard_grouping_and_unused_keys_filtering(self):
        """
        Vérifie le fonctionnement du dashboard personnalisé de l'espace client :
        - Les licences pour un même module sont regroupées en une seule ligne/tuile.
        - Les activations autorisées et utilisées sont cumulées.
        - Seules les clés inutilisées (non liées à une installation) s'affichent.
        - Une clé qui vient d'être activée disparaît automatiquement de l'écran.
        """
        # Création de deux licences (deux clés) pour le même utilisateur et module
        lic1 = License.objects.create(
            user=self.user,
            module=self.module,
            is_active=True,
            max_activations=1
        )
        lic2 = License.objects.create(
            user=self.user,
            module=self.module,
            is_active=True,
            max_activations=1
        )
        
        # --- ÉTAPE A : Les deux clés sont inutilisées ---
        response = self.client.get(reverse('users:dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Récupération du contexte
        licenses_list = response.context['licenses']
        self.assertEqual(len(licenses_list), 1)  # Une seule ligne affichée pour le module
        
        card = licenses_list[0]
        self.assertEqual(card['module'].id, self.module.id)
        self.assertEqual(card['total_max_activations'], 2)  # Cumul 1 + 1 = 2
        self.assertEqual(card['total_activation_count'], 0)  # Aucune activée
        self.assertEqual(len(card['unused_keys']), 2)  # Deux clés inutilisées affichées
        
        keys_displayed = [k['key'] for k in card['unused_keys']]
        self.assertIn(str(lic1.license_key), keys_displayed)
        self.assertIn(str(lic2.license_key), keys_displayed)

        # --- ÉTAPE B : Activation d'une clé (lic1) par une GMAO ---
        installation = Installation.objects.create(
            installation_uuid=uuid.uuid4(),
            user=self.user
        )
        lic1.installation = installation
        lic1.activation_count = 1
        lic1.save()
        
        # --- ÉTAPE C : Vérification de la disparition de la clé activée ---
        response = self.client.get(reverse('users:dashboard'), follow=True)
        licenses_list = response.context['licenses']
        card = licenses_list[0]
        
        # Le compteur doit être incrémenté à 1 / 2
        self.assertEqual(card['total_activation_count'], 1)
        self.assertEqual(card['total_max_activations'], 2)
        
        # Seule la clé 2 doit être affichée. La clé 1 doit avoir disparu de l'écran !
        self.assertEqual(len(card['unused_keys']), 1)
        self.assertEqual(card['unused_keys'][0]['key'], str(lic2.license_key))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LicenseAPITestCase(TestCase):
    def setUp(self):
        from catalog.models import CoreVersion, ModuleVersion
        import datetime

        self.user = User.objects.create_user(
            username='api_client',
            email='api_client@test.com',
            password='password123'
        )
        self.category = Category.objects.create(name='Sécurité', slug='securite')
        self.module = Module.objects.create(
            name='Contrôle d\'accès RFID',
            slug='controle-acces-rfid',
            price=120.00,
            category=self.category,
            is_active=True
        )
        self.core_version = CoreVersion.objects.create(version='1.0.0')
        self.module_version = ModuleVersion.objects.create(
            module=self.module,
            version_number='1.0.0',
            release_date=datetime.date.today(),
            min_core_version=self.core_version
        )
        self.license = License.objects.create(
            user=self.user,
            module=self.module,
            is_active=True,
            max_activations=1,
            activation_count=0
        )
        self.client_http = Client()

    def test_validate_license_api_success(self):
        """Vérifie la validation réussie d'une licence via l'API REST."""
        inst_uuid = str(uuid.uuid4())
        response = self.client_http.post(
            '/api/licensing/validate/',
            data={
                'license_key': str(self.license.license_key),
                'installation_uuid': inst_uuid
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('version'), '1.0.0')

        self.license.refresh_from_db()
        self.assertEqual(self.license.activation_count, 1)
        self.assertIsNotNone(self.license.installation)
        self.assertEqual(str(self.license.installation.installation_uuid), inst_uuid)

    def test_validate_license_api_quota_exceeded(self):
        """Vérifie le rejet (HTTP 403) lorsque la licence a déjà atteint son quota sur une autre installation."""
        inst1 = Installation.objects.create(installation_uuid=uuid.uuid4(), user=self.user)
        self.license.installation = inst1
        self.license.activation_count = 1
        self.license.save()

        # Tentative d'activation depuis une autre machine (installation_uuid distinct)
        different_uuid = str(uuid.uuid4())
        response = self.client_http.post(
            '/api/licensing/validate/',
            data={
                'license_key': str(self.license.license_key),
                'installation_uuid': different_uuid
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn("quota d'activations", data.get('error'))

    def test_license_database_constraint_integrity(self):
        """Vérifie que la CheckConstraint empêche activation_count > max_activations."""
        with self.assertRaises(IntegrityError):
            License.objects.create(
                user=self.user,
                module=self.module,
                is_active=True,
                max_activations=1,
                activation_count=2
            )


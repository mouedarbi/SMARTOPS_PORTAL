"""
Fichier : tests.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 1.2
Description : Tests unitaires pour l'authentification et le modèle User.
              Vérifie le fonctionnement de django-allauth et des champs personnalisés.
"""

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

User = get_user_model()

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountsTests(TestCase):
    """
    Tests pour l'application accounts.
    """

    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """
        Vérifie la création d'un utilisateur avec les champs personnalisés.
        """
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.language_preference, 'fr')
        self.assertTrue(user.is_client)

    def test_login_url_exists(self):
        """
        Vérifie que la page de connexion de allauth est accessible.
        """
        response = self.client.get(reverse('account_login'), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_signup_url_exists(self):
        """
        Vérifie que la page d'inscription de allauth est accessible.
        """
        response = self.client.get(reverse('account_signup'), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_login_functional(self):
        """
        Teste la fonctionnalité de connexion via le client Django.
        """
        login_success = self.client.login(username='test@example.com', password='testpassword123')
        self.assertTrue(login_success)
        
        # Vérifier que l'utilisateur est bien connecté dans la session
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_user_anonymize_gdpr_art_17(self):
        """
        Vérifie la conformité avec l'Article 17 du RGPD (Droit à l'oubli) :
        pseudonymisation, suppression des données personnelles et horodatage deleted_at.
        """
        user = User.objects.create_user(
            username='gdpr_user',
            email='gdpr_user@example.com',
            first_name='Jean',
            last_name='Dupont',
            password='password123'
        )
        user.anonymize()

        user.refresh_from_db()
        self.assertTrue(user.is_deleted)
        self.assertIsNotNone(user.deleted_at)
        self.assertFalse(user.is_active)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        self.assertTrue(user.email.startswith('deleted_'))
        self.assertTrue(user.username.startswith('deleted_'))

    def test_user_deleted_at_constraint_integrity(self):
        """
        Vérifie que la CheckConstraint empêche un is_deleted=True avec deleted_at=None.
        """
        with self.assertRaises(IntegrityError):
            User.objects.create(
                username='invalid_deleted_user',
                email='invalid_deleted@example.com',
                password='password123',
                is_deleted=True,
                deleted_at=None
            )

    def test_signup_form_post_creates_user(self):
        """F1 : Vérifie la création effective d'un compte utilisateur via soumission POST du formulaire."""
        signup_url = reverse('account_signup')
        data = {
            'username': 'nouveau_client',
            'email': 'nouveau@client.be',
            'password1': 'SecurPass12345!',
            'password2': 'SecurPass12345!'
        }
        response = self.client.post(signup_url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        created_user = User.objects.filter(username='nouveau_client').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.email, 'nouveau@client.be')
        self.assertTrue(created_user.is_client)

    def test_dashboard_view_displays_grouped_licenses_and_orders(self):
        """F1 : Vérifie l'accès au tableau de bord client et l'affichage structuré de ses licences et commandes."""
        from catalog.models import Category, Module
        from licensing.models import License
        from payments.models import Order
        from decimal import Decimal

        cat = Category.objects.create(name='Sécurité', slug='securite')
        mod = Module.objects.create(name='Module Badgeuse', slug='module-badgeuse', price=Decimal('99.00'), category=cat, is_active=True)
        lic = License.objects.create(user=self.user, module=mod, is_active=True, max_activations=2)
        order = Order.objects.create(user=self.user, status='completed', total_amount=Decimal('99.00'))

        self.client.force_login(self.user)
        response = self.client.get(reverse('users:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('licenses', response.context)
        self.assertIn('orders', response.context)
        self.assertEqual(len(response.context['licenses']), 1)
        self.assertEqual(response.context['licenses'][0]['module'], mod)


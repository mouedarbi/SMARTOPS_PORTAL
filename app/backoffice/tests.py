"""
Fichier : tests.py
Application : backoffice
Auteur : Mohamed Ouedarbi
Description : Tests unitaires pour l'accès et les fonctionnalités du tableau de bord administrateur (Backoffice).
"""

import uuid
from decimal import Decimal
from django.test import TestCase, Client as HttpClient, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from catalog.models import Category, Module
from payments.models import Order, OrderItem
from licensing.models import License, Installation

User = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BackofficeWorkflowTestCase(TestCase):
    def setUp(self):
        # 1. Administrateur
        self.admin_user = User.objects.create_superuser(
            username='admin_boss',
            email='admin@smartops.org',
            password='AdminPassword123!'
        )
        # 2. Utilisateur standard
        self.regular_user = User.objects.create_user(
            username='regular_client',
            email='client@test.com',
            password='ClientPassword123!'
        )
        # 3. Données de démonstration
        self.category = Category.objects.create(name='Analytics', slug='analytics')
        self.module = Module.objects.create(
            name='Module Dashboard BI',
            slug='module-dashboard-bi',
            price=Decimal('200.00'),
            category=self.category,
            is_active=True
        )
        self.order = Order.objects.create(
            user=self.regular_user,
            status='completed',
            total_amount=Decimal('200.00')
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            module=self.module,
            price_at_purchase=Decimal('200.00')
        )
        self.license = License.objects.create(
            user=self.regular_user,
            module=self.module,
            is_active=True,
            max_activations=1
        )
        self.installation = Installation.objects.create(
            installation_uuid=uuid.uuid4(),
            user=self.regular_user,
            company_name='Entreprise Test'
        )

        self.client_http = HttpClient()

    def test_backoffice_access_restricted_to_admin(self):
        """Vérifie que les utilisateurs non-administrateurs sont redirigés/bloqués."""
        self.client_http.login(username='regular_client', password='ClientPassword123!')
        response = self.client_http.get('/fr/backoffice/')
        # Redirection vers la page de login par user_passes_test
        self.assertEqual(response.status_code, 302)

    def test_backoffice_index_statistics_for_admin(self):
        """Vérifie l'accès au tableau de bord administrateur et le calcul des statistiques."""
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get('/fr/backoffice/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_products'], 1)
        self.assertEqual(response.context['total_sales'], 1)
        self.assertEqual(response.context['total_licenses'], 1)
        self.assertEqual(response.context['total_earnings'], Decimal('200.00'))

    def test_backoffice_installations_monitoring(self):
        """Vérifie la consultation de la liste des installations par un administrateur."""
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get('/fr/backoffice/installations/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entreprise Test')

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

from django.utils import timezone

from catalog.models import Category, Module
from payments.models import Order, OrderItem
from licensing.models import License, Installation, SupportSubscription

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

    def test_support_subscription_search_restricted_to_admin(self):
        """Vérifie que la recherche d'abonnement support est réservée aux administrateurs."""
        self.client_http.login(username='regular_client', password='ClientPassword123!')
        response = self.client_http.get(reverse('backoffice:support_subscription_search'))
        self.assertEqual(response.status_code, 302)

    def test_support_subscription_search_found_redirects_to_user_detail(self):
        """Une recherche par email existant redirige vers la fiche client (où le statut est affiché)."""
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(
            reverse('backoffice:support_subscription_search'), {'email': self.regular_user.email}
        )
        self.assertRedirects(response, reverse('backoffice:user_detail', kwargs={'pk': self.regular_user.pk}))

    def test_support_subscription_search_not_found_shows_message(self):
        """Une recherche par email inconnu réaffiche le formulaire avec un message, sans redirection."""
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(
            reverse('backoffice:support_subscription_search'), {'email': 'inconnu@nowhere.com'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aucun client trouvé')

    def test_user_detail_shows_active_and_expired_support_subscriptions(self):
        """La fiche client affiche correctement plusieurs abonnements support (actif et expiré)."""
        module_2 = Module.objects.create(
            name='Module Dashboard BI 2',
            slug='module-dashboard-bi-2',
            price=Decimal('150.00'),
            category=self.category,
            is_active=True
        )
        SupportSubscription.objects.create(
            user=self.regular_user, module=self.module,
            expires_at=timezone.now() + timezone.timedelta(days=100),
            amount_paid=Decimal('49.00')
        )
        SupportSubscription.objects.create(
            user=self.regular_user, module=module_2,
            expires_at=timezone.now() - timezone.timedelta(days=10),
            amount_paid=Decimal('49.00')
        )

        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(reverse('backoffice:user_detail', kwargs={'pk': self.regular_user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Actif')
        self.assertContains(response, 'Expiré')

    def test_order_detail_shows_support_badge_only_on_support_items(self):
        """order_detail affiche le badge 'Support annuel' uniquement sur les OrderItem concernés."""
        support_order = Order.objects.create(
            user=self.regular_user, status='completed', total_amount=Decimal('49.00')
        )
        OrderItem.objects.create(
            order=support_order, module=self.module,
            price_at_purchase=Decimal('49.00'), product_type='support'
        )

        self.client_http.login(username='admin_boss', password='AdminPassword123!')

        response_module = self.client_http.get(reverse('backoffice:order_detail', kwargs={'pk': self.order.pk}))
        self.assertNotContains(response_module, 'Support annuel')

        response_support = self.client_http.get(reverse('backoffice:order_detail', kwargs={'pk': support_order.pk}))
        self.assertContains(response_support, 'Support annuel')

    def test_support_subscription_search_lists_clients_with_support(self):
        """La page Support Client liste les clients ayant au moins un abonnement, avec leurs compteurs, et pas les autres."""
        SupportSubscription.objects.create(
            user=self.regular_user, module=self.module,
            expires_at=timezone.now() + timezone.timedelta(days=100),
            amount_paid=Decimal('49.00')
        )
        no_support_user = User.objects.create_user(
            username='no_support_client', email='no_support@test.com', password='Pwd123456!'
        )

        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(reverse('backoffice:support_subscription_search'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.regular_user.username)
        self.assertNotContains(response, no_support_user.username)
        self.assertIn(self.regular_user, list(response.context['clients']))
        client_row = next(c for c in response.context['clients'] if c.id == self.regular_user.id)
        self.assertEqual(client_row.support_active_count, 1)
        self.assertEqual(client_row.support_total_count, 1)
        self.assertIn(
            reverse('backoffice:user_detail', kwargs={'pk': self.regular_user.pk}),
            response.content.decode()
        )

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


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ModuleSalesDetailTestCase(TestCase):
    """Page « Détail des ventes » d'un module (issue #8)."""

    def setUp(self):
        from catalog.models import ModuleBundle
        self.admin = User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.alice = User.objects.create_user('alice', 'alice@example.org', 'Password123!')
        self.bob = User.objects.create_user('bob', 'bob@example.org', 'Password123!')
        category = Category.objects.create(name='Analytics', slug='analytics')
        self.module = Module.objects.create(
            name='Module BI', slug='module-bi', price=Decimal('200.00'),
            support_annual_price=Decimal('40.00'), category=category, is_active=True,
        )
        self.other = Module.objects.create(
            name='Autre module', slug='autre-module', price=Decimal('10.00'), category=category, is_active=True,
        )
        # Alice : achat direct terminé + licence
        self.order_alice = Order.objects.create(
            user=self.alice, status='completed', total_amount=Decimal('200.00'),
            stripe_payment_intent_id='pi_alice_123', withdrawal_waiver_accepted_at=timezone.now(),
        )
        OrderItem.objects.create(order=self.order_alice, module=self.module, price_at_purchase=Decimal('200.00'))
        self.license = License.objects.create(user=self.alice, module=self.module)
        # Bob : achat via un pack contenant le module
        bundle = ModuleBundle.objects.create(
            name='Pack Analyse', slug='pack-analyse', short_description='x', description='x',
        )
        bundle.modules.add(self.module, self.other)
        self.order_bob = Order.objects.create(user=self.bob, status='completed', total_amount=Decimal('150.00'))
        OrderItem.objects.create(order=self.order_bob, bundle=bundle, price_at_purchase=Decimal('150.00'))
        # Alice : support annuel remboursé
        self.order_support = Order.objects.create(user=self.alice, status='refunded', total_amount=Decimal('40.00'))
        OrderItem.objects.create(
            order=self.order_support, module=self.module, price_at_purchase=Decimal('40.00'), product_type='support',
        )
        # Vente d'un autre module : ne doit pas apparaître
        self.order_other = Order.objects.create(user=self.bob, status='completed', total_amount=Decimal('10.00'))
        OrderItem.objects.create(order=self.order_other, module=self.other, price_at_purchase=Decimal('10.00'))
        self.url = reverse('backoffice:module_sales', kwargs={'pk': self.module.pk})
        self.client_http = HttpClient()

    def test_requires_admin(self):
        self.client_http.login(username='alice', password='Password123!')
        self.assertNotEqual(self.client_http.get(self.url).status_code, 200)
        self.client_http.logout()
        self.assertNotEqual(self.client_http.get(self.url).status_code, 200)

    def test_lists_direct_bundle_and_support_sales_of_this_module_only(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(self.url)
        self.assertEqual(response.status_code, 200)
        ids = {item.order_id for item in response.context['page']}
        self.assertEqual(ids, {self.order_alice.id, self.order_bob.id, self.order_support.id})
        self.assertNotIn(self.order_other.id, ids)
        self.assertContains(response, 'alice@example.org')
        self.assertContains(response, 'Pack Analyse')

    def test_statistics(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        stats = self.client_http.get(self.url).context['stats']
        self.assertEqual(stats['direct_count'], 1)
        self.assertEqual(stats['bundle_count'], 1)
        self.assertEqual(stats['support_count'], 0)   # le support est remboursé : non compté
        self.assertEqual(stats['direct_revenue'], Decimal('200.00'))
        self.assertEqual(stats['buyers_count'], 2)
        self.assertEqual(stats['refunded_count'], 1)

    def test_license_key_and_waiver_shown_for_buyer(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(self.url)
        self.assertContains(response, str(self.license.license_key))

    def test_search_by_email_username_order_id_and_payment_reference(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        cases = {
            'alice@example.org': {self.order_alice.id, self.order_support.id},
            'bob': {self.order_bob.id},
            f'#{self.order_bob.id}': {self.order_bob.id},
            'pi_alice_123': {self.order_alice.id},
        }
        for query, expected in cases.items():
            response = self.client_http.get(self.url, {'q': query})
            self.assertEqual({i.order_id for i in response.context['page']}, expected, query)
        response = self.client_http.get(self.url, {'q': 'inconnu@nowhere.tld'})
        self.assertContains(response, 'Aucune vente ne correspond')

    def test_modules_list_links_to_sales_page(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(reverse('backoffice:module_list'))
        self.assertContains(response, self.url)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ContactMessagesBackofficeTestCase(TestCase):
    """Page « Messages contact » du backoffice (issue #6)."""

    def setUp(self):
        from core.models import ContactMessage
        self.admin = User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.user = User.objects.create_user('regular', 'r@example.org', 'Password123!')
        self.unread = ContactMessage.objects.create(name='Alice', email='alice@example.org', message='Message non lu')
        self.read = ContactMessage.objects.create(name='Bob', email='bob@example.org', message='Message lu', is_read=True)
        self.list_url = reverse('backoffice:contact_message_list')
        self.client_http = HttpClient()

    def test_requires_admin(self):
        self.assertNotEqual(self.client_http.get(self.list_url).status_code, 200)
        self.client_http.login(username='regular', password='Password123!')
        self.assertNotEqual(self.client_http.get(self.list_url).status_code, 200)

    def test_lists_messages_and_filters_unread(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        response = self.client_http.get(self.list_url)
        self.assertContains(response, 'alice@example.org')
        self.assertContains(response, 'bob@example.org')
        response = self.client_http.get(self.list_url, {'unread': '1'})
        self.assertContains(response, 'alice@example.org')
        self.assertNotContains(response, 'bob@example.org')
        self.assertEqual(response.context['unread_count'], 1)

    def test_toggle_read_requires_post_and_flips_state(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        url = reverse('backoffice:contact_message_toggle_read', kwargs={'pk': self.unread.pk})
        self.assertEqual(self.client_http.get(url).status_code, 405)
        self.client_http.post(url)
        self.unread.refresh_from_db()
        self.assertTrue(self.unread.is_read)
        self.client_http.post(url)
        self.unread.refresh_from_db()
        self.assertFalse(self.unread.is_read)

    def test_toggle_read_refuses_external_redirect(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        url = reverse('backoffice:contact_message_toggle_read', kwargs={'pk': self.unread.pk})
        response = self.client_http.post(url, {'next': 'https://evil.example/phish'})
        self.assertEqual(response['Location'], self.list_url)

    def test_sidebar_links_to_messages(self):
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        self.assertContains(self.client_http.get(reverse('backoffice:index')), self.list_url)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BackofficeI18nTestCase(TestCase):
    """Le backoffice est disponible en français, anglais et néerlandais (issue #12)."""

    def setUp(self):
        self.admin = User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')

    def _get(self, lang, name='backoffice:index'):
        from django.utils import translation
        with translation.override(lang):
            url = reverse(name)
        return url, self.client_http.get(url).content.decode()

    def test_dashboard_is_translated_in_three_languages(self):
        expected = {
            'fr': ('Dernières Transactions', 'Tableau de bord'),
            'en': ('Latest Transactions', 'Dashboard'),
            'nl': ('Laatste transacties', 'Dashboard'),
        }
        for lang, (latest, menu) in expected.items():
            url, html = self._get(lang)
            self.assertTrue(url.startswith(f'/{lang}/backoffice/'))
            self.assertIn(f'<html lang="{lang}">', html)
            self.assertIn(latest, html, lang)
            self.assertIn(menu, html, lang)
        # Pas de résidu français en anglais / néerlandais dans la navigation
        for lang in ('en', 'nl'):
            _, html = self._get(lang)
            for french in ('Opérations', 'Modération Avis', "Journal d'Audit", 'Packs promotionnels'):
                self.assertNotIn(french, html, f'{french} en {lang}')

    def test_language_switcher_is_present_and_keeps_current_page(self):
        _, html = self._get('en', 'backoffice:module_list')
        for code in ('fr', 'en', 'nl'):
            self.assertIn(f'name="language" type="hidden" value="{code}"', html)
        self.assertIn('action="/i18n/setlang/"', html)
        self.assertIn('name="next" type="hidden" value="/backoffice/modules/"', html)

    def test_switching_language_redirects_to_same_page_in_new_language(self):
        response = self.client_http.post('/i18n/setlang/', {'language': 'nl', 'next': '/backoffice/modules/'}, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], '/nl/backoffice/modules/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<html lang="nl">', response.content.decode())

    def test_dates_follow_the_language_format(self):
        user = User.objects.create_user('buyer', 'b@example.org', 'Password123!')
        order = Order.objects.create(user=user, status='completed', total_amount=Decimal('10.00'))
        Order.objects.filter(pk=order.pk).update(created_at=timezone.make_aware(timezone.datetime(2026, 3, 7, 14, 5)))
        self.assertIn('07/03/2026 14:05', self._get('fr')[1])
        self.assertIn('7-3-2026 14:05', self._get('nl')[1])
        self.assertIn('03/07/2026', self._get('en')[1])

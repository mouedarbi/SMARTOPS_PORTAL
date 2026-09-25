"""
Fichier : tests.py
Application : backoffice
Auteur : Mohamed Ouedarbi
Description : Tests unitaires pour l'accès et les fonctionnalités du tableau de bord administrateur (Backoffice).
"""

import re
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
class BackofficeI18nTestCase(TestCase):
    """Le backoffice est disponible en français, anglais et néerlandais (issue #12)."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')  # le middleware laisse la dernière langue active
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


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BackofficeMessagesTestCase(TestCase):
    """Les messages de confirmation s'affichent dans le backoffice, une seule fois."""

    def setUp(self):
        from django.utils import translation
        translation.activate('fr')
        self.addCleanup(translation.activate, 'fr')
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        self.category = Category.objects.create(name='Analytics', slug='analytics')

    def test_success_message_is_displayed_once_after_an_action(self):
        url = reverse('backoffice:category_delete', kwargs={'pk': self.category.pk})
        response = self.client_http.post(url, follow=True)
        self.assertContains(response, 'Catégorie supprimée.')
        self.assertContains(response, 'bg-amber-50')  # avertissement : style dédié
        again = self.client_http.get(reverse('backoffice:category_list'))
        self.assertNotContains(again, 'Catégorie supprimée.')

    def test_messages_do_not_leak_onto_other_pages(self):
        self.client_http.post(reverse('backoffice:category_delete', kwargs={'pk': self.category.pk}))
        # La page des avis ne doit pas « découvrir » un message resté en attente : il est affiché ici, une fois.
        page = self.client_http.get(reverse('backoffice:module_list'))
        self.assertContains(page, 'Catégorie supprimée.')
        self.assertNotContains(self.client_http.get(reverse('backoffice:reviews_list')), 'Catégorie supprimée.')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CatalogBackofficeI18nTestCase(TestCase):
    """Écrans du catalogue (modules, packs, catégories, versions du Core) traduits (issue #13)."""

    PAGES = ('backoffice:module_list', 'backoffice:module_create', 'backoffice:bundle_list', 'backoffice:bundle_create',
             'backoffice:category_list', 'backoffice:category_create', 'backoffice:core_version_list',
             'backoffice:core_version_create')
    FRENCH_MARKERS = ('Enregistrer', 'Annuler', 'Nouveau ', 'Nouvelle ', 'Gestion des', 'Retour', 'Aucun', 'Supprimer',
                      'Paramètres', 'Modifier', 'Gérez', 'Suivez', 'Organisez')

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        self.category = Category.objects.create(name='Analytics', slug='analytics')

    def _url(self, lang, name, **kwargs):
        from django.utils import translation
        with translation.override(lang):
            return reverse(name, kwargs=kwargs)

    def test_pages_have_no_french_left_in_english_and_dutch(self):
        for lang in ('en', 'nl'):
            for name in self.PAGES:
                response = self.client_http.get(self._url(lang, name))
                self.assertEqual(response.status_code, 200, f'{name} {lang}')
                html = re.sub(r'<!--.*?-->', '', response.content.decode(), flags=re.S)  # commentaires invisibles
                for marker in self.FRENCH_MARKERS:
                    found = re.search(rf'\b{re.escape(marker.strip())}\b', html)
                    context = html[max(0, found.start() - 60):found.start() + 60].replace('\n', ' ') if found else ''
                    self.assertIsNone(found, f'« {marker.strip()} » trouvé dans {name} en {lang} : …{context}…')

    def test_forms_show_translated_labels(self):
        cases = {
            'fr': {'backoffice:module_create': ('Enregistrer', 'Prix de vente (€)'), 'backoffice:category_create': ('Enregistrer la catégorie',)},
            'en': {'backoffice:module_create': ('Save', 'Sale price (€)', 'Module name (EN)'), 'backoffice:category_create': ('Save category',)},
            'nl': {'backoffice:module_create': ('Opslaan', 'Verkoopprijs (€)', 'Modulenaam (NL)'), 'backoffice:category_create': ('Categorie opslaan',)},
        }
        for lang, pages in cases.items():
            for name, expected in pages.items():
                html = self.client_http.get(self._url(lang, name)).content.decode()
                for text in expected:
                    self.assertIn(text, html, f'{text} / {name} / {lang}')

    def test_bundle_discount_mode_options_are_translated(self):
        expected = {'fr': 'Remise en pourcentage sur le total', 'en': 'Percentage discount on the total',
                    'nl': 'Procentuele korting op het totaal'}
        for lang, text in expected.items():
            self.assertContains(self.client_http.get(self._url(lang, 'backoffice:bundle_create')), text)

    def test_confirmation_messages_follow_the_language(self):
        expected = {'fr': 'Catégorie supprimée.', 'en': 'Category deleted.', 'nl': 'Categorie verwijderd.'}
        for lang, text in expected.items():
            cat = Category.objects.create(name=f'Temp {lang}', slug=f'temp-{lang}')
            response = self.client_http.post(self._url(lang, 'backoffice:category_delete', pk=cat.pk), follow=True)
            self.assertContains(response, text)

    def test_core_version_dates_use_local_format(self):
        from datetime import date
        from catalog.models import CoreVersion
        version = CoreVersion.objects.create(version='2.4.0')
        CoreVersion.objects.filter(pk=version.pk).update(release_date=date(2026, 3, 7))  # auto_now_add
        self.assertContains(self.client_http.get(self._url('fr', 'backoffice:core_version_list')), '07/03/2026')
        self.assertContains(self.client_http.get(self._url('nl', 'backoffice:core_version_list')), '7-3-2026')
        self.assertContains(self.client_http.get(self._url('en', 'backoffice:core_version_list')), '03/07/2026')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConfirmDeletePagesTestCase(TestCase):
    """Supprimer une catégorie ou un pack ouvre une page de confirmation (elle n'existait pas)."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        from catalog.models import ModuleBundle
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')
        self.category = Category.objects.create(name='Analytics', slug='analytics')
        self.bundle = ModuleBundle.objects.create(name='Pack Analyse', slug='pack-analyse', short_description='x', description='x')

    def test_category_delete_shows_confirmation_page_then_deletes_on_post(self):
        url = reverse('backoffice:category_delete', kwargs={'pk': self.category.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics')
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())  # GET ne supprime rien
        self.client_http.post(url)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_bundle_delete_shows_confirmation_page_then_deletes_on_post(self):
        from catalog.models import ModuleBundle
        url = reverse('backoffice:bundle_delete', kwargs={'pk': self.bundle.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pack Analyse')
        self.assertTrue(ModuleBundle.objects.filter(pk=self.bundle.pk).exists())
        self.client_http.post(url)
        self.assertFalse(ModuleBundle.objects.filter(pk=self.bundle.pk).exists())

    def test_confirmation_pages_are_translated(self):
        from django.utils import translation
        for lang, title in (('en', 'Delete'), ('nl', 'verwijderen')):
            for name, pk in (('backoffice:category_delete', self.category.pk), ('backoffice:bundle_delete', self.bundle.pk)):
                with translation.override(lang):
                    url = reverse(name, kwargs={'pk': pk})
                html = self.client_http.get(url).content.decode()
                self.assertIn(title, html, f'{name} {lang}')
                self.assertNotIn('Supprimer', html, f'{name} {lang}')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CustomersSalesBackofficeI18nTestCase(TestCase):
    """Écrans clients et ventes (commandes, licences, installations, support, utilisateurs) traduits (issue #14)."""

    FRENCH_MARKERS = ('Aucun', 'Aucune', 'Retour', 'Modifier', 'Supprimer', 'Enregistrer', 'Historique', 'Suivi',
                      'Gestion', 'Consultez', 'Supervisez', 'Recherchez', 'Cliquez', 'Attention', 'Licences',
                      'Commandes', 'Utilisateur')

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        self.admin = User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.buyer = User.objects.create_user('buyer', 'buyer@example.org', 'Password123!')
        category = Category.objects.create(name='Analytics', slug='analytics')
        self.module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('200.00'), category=category, is_active=True)
        self.order = Order.objects.create(user=self.buyer, status='refunded', total_amount=Decimal('200.00'),
                                          stripe_payment_intent_id='pi_test_1', withdrawal_waiver_accepted_at=timezone.now())
        OrderItem.objects.create(order=self.order, module=self.module, price_at_purchase=Decimal('200.00'))
        License.objects.create(user=self.buyer, module=self.module)
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')

    def _url(self, lang, name, **kwargs):
        from django.utils import translation
        with translation.override(lang):
            return reverse(name, kwargs=kwargs)

    def _pages(self):
        return [('backoffice:order_list', {}), ('backoffice:order_detail', {'pk': self.order.pk}),
                ('backoffice:license_list', {}), ('backoffice:installation_list', {}),
                ('backoffice:support_subscription_search', {}), ('backoffice:module_sales', {'pk': self.module.pk}),
                ('backoffice:user_list', {}), ('backoffice:user_detail', {'pk': self.buyer.pk}),
                ('backoffice:user_edit', {'pk': self.buyer.pk}), ('backoffice:user_delete', {'pk': self.buyer.pk})]

    def test_pages_have_no_french_left_in_english_and_dutch(self):
        for lang in ('en', 'nl'):
            for name, kwargs in self._pages():
                response = self.client_http.get(self._url(lang, name, **kwargs))
                self.assertEqual(response.status_code, 200, f'{name} {lang}')
                html = re.sub(r'<!--.*?-->', '', response.content.decode(), flags=re.S)  # commentaires invisibles
                for marker in self.FRENCH_MARKERS:
                    found = re.search(rf'\b{re.escape(marker)}\b', html)
                    context = html[max(0, found.start() - 60):found.start() + 60].replace('\n', ' ') if found else ''
                    self.assertIsNone(found, f'« {marker} » trouvé dans {name} en {lang} : …{context}…')

    def test_order_status_is_translated_not_raw(self):
        expected = {'fr': 'Remboursée', 'en': 'Refunded', 'nl': 'Terugbetaald'}
        for lang, label in expected.items():
            for name, kwargs in (('backoffice:order_list', {}), ('backoffice:order_detail', {'pk': self.order.pk})):
                html = self.client_http.get(self._url(lang, name, **kwargs)).content.decode()
                self.assertIn(label, html, f'{name} {lang}')
                self.assertNotIn('>refunded<', html)

    def test_sales_page_dynamic_sentences(self):
        html = self.client_http.get(self._url('en', 'backoffice:module_sales', pk=self.module.pk), {'q': 'nobody@nowhere'}).content.decode()
        self.assertIn('No sale matches “nobody@nowhere”.', html)
        nl = self.client_http.get(self._url('nl', 'backoffice:module_sales', pk=self.module.pk)).content.decode()
        self.assertIn('Afstand herroepingsrecht', nl)
        self.assertIn('1 terugbetaald', nl)

    def test_user_messages_follow_the_language(self):
        expected = {'fr': "a été supprimé", 'en': 'has been deleted', 'nl': 'is verwijderd'}
        for lang, text in expected.items():
            victim = User.objects.create_user(f'victim_{lang}', f'v_{lang}@example.org', 'Password123!')
            response = self.client_http.post(self._url(lang, 'backoffice:user_delete', pk=victim.pk), follow=True)
            self.assertContains(response, text)

    def test_dates_use_the_local_format(self):
        Order.objects.filter(pk=self.order.pk).update(created_at=timezone.make_aware(timezone.datetime(2026, 3, 7, 14, 5)))
        self.assertContains(self.client_http.get(self._url('fr', 'backoffice:order_list')), '07/03/2026 14:05')
        self.assertContains(self.client_http.get(self._url('nl', 'backoffice:order_list')), '7-3-2026 14:05')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ModerationFollowUpBackofficeI18nTestCase(TestCase):
    """Modération (avis) et suivi (journaux) traduits + vérification d'ensemble (issue #15)."""

    FRENCH_MARKERS = ('Aucun', 'Aucune', 'Retour', 'Modifier', 'Supprimer', 'Enregistrer', 'Modération', 'Validez',
                      'Approuver', 'Rejeter', 'Actualiser', 'Vider', 'Marquer', 'Journal', 'Surveillance', 'Trace')

    def setUp(self):
        from django.utils import translation
        from catalog.models import Review
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        self.admin = User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.buyer = User.objects.create_user('buyer', 'buyer@example.org', 'Password123!')
        category = Category.objects.create(name='Analytics', slug='analytics')
        self.module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('10.00'), category=category, is_active=True)
        self.review = Review.objects.create(user=self.buyer, module=self.module, rating=4, comment='Très bien')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')

    def _url(self, lang, name, **kwargs):
        from django.utils import translation
        with translation.override(lang):
            return reverse(name, kwargs=kwargs)

    def test_pages_have_no_french_left_in_english_and_dutch(self):
        for lang in ('en', 'nl'):
            for name in ('backoffice:reviews_list', 'backoffice:logs_view'):
                response = self.client_http.get(self._url(lang, name))
                self.assertEqual(response.status_code, 200, f'{name} {lang}')
                html = re.sub(r'<!--.*?-->', '', response.content.decode(), flags=re.S)  # commentaires invisibles
                for marker in self.FRENCH_MARKERS:
                    found = re.search(rf'\b{re.escape(marker)}\b', html)
                    context = html[max(0, found.start() - 60):found.start() + 60].replace('\n', ' ') if found else ''
                    self.assertIsNone(found, f'« {marker} » trouvé dans {name} en {lang} : …{context}…')

    def test_key_labels_in_three_languages(self):
        expected = {
            'fr': {'backoffice:reviews_list': 'Rejeter', 'backoffice:logs_view': 'Vider les logs'},
            'en': {'backoffice:reviews_list': 'Reject', 'backoffice:logs_view': 'Clear logs'},
            'nl': {'backoffice:reviews_list': 'Afwijzen', 'backoffice:logs_view': 'Logs wissen'},
        }
        for lang, pages in expected.items():
            for name, text in pages.items():
                self.assertContains(self.client_http.get(self._url(lang, name)), text)

    def test_review_rating_header_is_not_mistranslated_as_a_note(self):
        # « Note » (texte) est déjà traduit « Notitie » au catalogue du projet : l'en-tête utilise « Évaluation ».
        self.assertContains(self.client_http.get(self._url('nl', 'backoffice:reviews_list')), 'Beoordeling')
        self.assertNotContains(self.client_http.get(self._url('nl', 'backoffice:reviews_list')), 'Notitie')

    def test_dynamic_sentences_and_messages(self):
        expected = {'fr': "a été rejeté/supprimé", 'en': 'rejected/deleted successfully', 'nl': 'afgewezen/verwijderd'}
        for lang, text in expected.items():
            from catalog.models import Review
            review = Review.objects.create(user=self.buyer, module=self.module, rating=3, comment='x')
            response = self.client_http.get(self._url(lang, 'backoffice:review_delete', pk=review.pk), follow=True)
            self.assertContains(response, text)

    def test_confirm_dialog_strings_are_javascript_safe(self):
        html = self.client_http.get(self._url('en', 'backoffice:logs_view')).content.decode()
        # l'apostrophe de « l'historique » ne doit pas casser la chaîne JavaScript du confirm()
        self.assertIn("confirm('Do you really want to clear the entire log history (application and database)?", html)

    def test_every_backoffice_screen_answers_in_the_three_languages(self):
        names = [('backoffice:index', {}), ('backoffice:module_list', {}), ('backoffice:module_create', {}),
                 ('backoffice:bundle_list', {}), ('backoffice:category_list', {}), ('backoffice:core_version_list', {}),
                 ('backoffice:order_list', {}), ('backoffice:license_list', {}), ('backoffice:installation_list', {}),
                 ('backoffice:support_subscription_search', {}), ('backoffice:user_list', {}),
                 ('backoffice:user_detail', {'pk': self.buyer.pk}), ('backoffice:module_sales', {'pk': self.module.pk}),
                 ('backoffice:reviews_list', {}), ('backoffice:logs_view', {})]
        for lang in ('fr', 'en', 'nl'):
            for name, kwargs in names:
                response = self.client_http.get(self._url(lang, name, **kwargs))
                self.assertEqual(response.status_code, 200, f'{name} {lang}')
                self.assertIn(f'<html lang="{lang}">', response.content.decode())


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DashboardCardsTestCase(TestCase):
    """Les cartes de statistiques du dashboard sont cliquables et la liste des transactions se filtre (issue #18)."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.buyer = User.objects.create_user('buyer', 'buyer@example.org', 'Password123!')
        self.completed = Order.objects.create(user=self.buyer, status='completed', total_amount=Decimal('50.00'))
        self.pending = Order.objects.create(user=self.buyer, status='pending', total_amount=Decimal('20.00'))
        self.refunded = Order.objects.create(user=self.buyer, status='refunded', total_amount=Decimal('10.00'))
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')

    def test_all_four_stat_cards_are_links(self):
        html = self.client_http.get(reverse('backoffice:index')).content.decode()
        completed_url = reverse('backoffice:order_list') + '?status=completed'
        for target in (reverse('backoffice:module_list'), completed_url, reverse('backoffice:license_list')):
            self.assertIn(f'<a href="{target}" class="block bg-white p-6', html, target)
        self.assertEqual(html.count('<a href="' + completed_url + '" class="block bg-white p-6'), 2)  # revenus + ventes
        self.assertNotIn('<div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md', html)

    def test_successful_sales_card_leads_to_completed_orders_only(self):
        response = self.client_http.get(reverse('backoffice:order_list'), {'status': 'completed'})
        self.assertEqual({o.id for o in response.context['orders']}, {self.completed.id})
        self.assertEqual(response.context['status_filter'], 'completed')

    def test_status_filter_tabs_and_invalid_value(self):
        response = self.client_http.get(reverse('backoffice:order_list'))
        self.assertEqual(len(response.context['orders']), 3)
        for value in ('pending', 'completed', 'failed', 'refunded'):
            self.assertContains(response, f'?status={value}')
        bad = self.client_http.get(reverse('backoffice:order_list'), {'status': 'hack'})
        self.assertEqual(len(bad.context['orders']), 3)
        self.assertEqual(bad.context['status_filter'], '')

    def test_filter_labels_are_translated(self):
        from django.utils import translation
        for lang, label in (('en', 'Completed'), ('nl', 'Voltooid')):
            with translation.override(lang):
                url = reverse('backoffice:order_list')
            self.assertContains(self.client_http.get(url, {'status': 'completed'}), label)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BackToSiteButtonTestCase(TestCase):
    """Un bouton ramène du backoffice vers le site public, dans la langue courante (issue #19)."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')

    def test_button_points_to_home_in_current_language_on_every_screen(self):
        from django.utils import translation
        labels = {'fr': 'Voir le site', 'en': 'View site', 'nl': 'Website bekijken'}
        for lang, label in labels.items():
            for name in ('backoffice:index', 'backoffice:module_list', 'backoffice:order_list', 'backoffice:logs_view'):
                with translation.override(lang):
                    url = reverse(name)
                html = self.client_http.get(url).content.decode()
                self.assertIn(f'<a href="/{lang}/" class="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100', html, f'{name} {lang}')
                self.assertIn(label, html, f'{name} {lang}')

    def test_the_target_page_answers(self):
        for lang in ('fr', 'en', 'nl'):
            self.assertEqual(self.client_http.get(f'/{lang}/').status_code, 200)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class NoFakeSearchBarTestCase(TestCase):
    """L'en-tête du backoffice ne contient plus de champ de recherche factice (issue #20)."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')

    def test_header_has_no_placeholder_search_input(self):
        from django.utils import translation
        for lang in ('fr', 'en', 'nl'):
            with translation.override(lang):
                url = reverse('backoffice:index')
            html = self.client_http.get(url).content.decode()
            header = html[html.index('<header'):html.index('</header>')]
            self.assertNotIn('<input type="text"', header, lang)
            self.assertNotIn('la-search', header, lang)
            for placeholder in ('Rechercher...', 'Search...', 'Zoeken...'):
                self.assertNotIn(placeholder, html, f'{placeholder} ({lang})')

    def test_real_searches_are_still_there(self):
        # Support client et détail des ventes gardent leur vraie recherche.
        self.assertContains(self.client_http.get(reverse('backoffice:support_subscription_search')), 'la-search')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BackofficePaginationTestCase(TestCase):
    """Pagination 10 / 50 / 100 sur toutes les listes du backoffice (issue #21)."""

    N = 60

    def setUp(self):
        from datetime import timedelta
        from django.utils import translation
        from catalog.models import CoreVersion, ModuleBundle, Review
        from backoffice.models import DatabaseAuditLog
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        self.admin = User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        category = Category.objects.create(name='Base', slug='base')
        self.module = Module.objects.create(name='Module 0', slug='module-0', price=Decimal('10.00'), category=category, is_active=True)
        for i in range(1, self.N):
            Module.objects.create(name=f'Module {i}', slug=f'module-{i}', price=Decimal('10.00'), category=category, is_active=True)
            Category.objects.create(name=f'Cat {i}', slug=f'cat-{i}')
            ModuleBundle.objects.create(name=f'Pack {i}', slug=f'pack-{i}', short_description='x', description='x')
        ModuleBundle.objects.create(name='Pack 0', slug='pack-0', short_description='x', description='x')
        User.objects.bulk_create([User(username=f'user{i}', email=f'user{i}@example.org') for i in range(self.N)])
        users = list(User.objects.filter(username__startswith='user'))
        Order.objects.bulk_create([Order(user=users[i], status='completed', total_amount=Decimal('5.00')) for i in range(self.N)])
        orders = list(Order.objects.all())
        OrderItem.objects.bulk_create([OrderItem(order=o, module=self.module, price_at_purchase=Decimal('5.00')) for o in orders])
        License.objects.bulk_create([License(user=users[i], module=self.module) for i in range(self.N)])
        Installation.objects.bulk_create([Installation(user=users[i], installation_uuid=uuid.uuid4()) for i in range(self.N)])
        SupportSubscription.objects.bulk_create([
            SupportSubscription(user=users[i], module=self.module, expires_at=timezone.now() + timedelta(days=30), amount_paid=Decimal('9.00'))
            for i in range(self.N)])
        CoreVersion.objects.bulk_create([CoreVersion(version=f'2.{i}.0') for i in range(self.N)])
        DatabaseAuditLog.objects.bulk_create([DatabaseAuditLog(action='INSERT', table_name='t', row_id=i) for i in range(self.N)])
        for i in range(self.N):
            Review.objects.create(user=users[i], module=self.module, rating=5, comment='ok')
        self.client_http = HttpClient()
        self.client_http.login(username='admin_boss', password='AdminPassword123!')

    def _lists(self):
        return {name: reverse(name, kwargs=kw) for name, kw in (
            ('backoffice:module_list', {}), ('backoffice:bundle_list', {}), ('backoffice:category_list', {}),
            ('backoffice:core_version_list', {}), ('backoffice:order_list', {}), ('backoffice:license_list', {}),
            ('backoffice:installation_list', {}), ('backoffice:support_subscription_search', {}),
            ('backoffice:user_list', {}), ('backoffice:reviews_list', {}),
            ('backoffice:logs_view', {}), ('backoffice:module_sales', {'pk': self.module.pk}))}

    def _page(self, url, **params):
        response = self.client_http.get(url, params)
        self.assertEqual(response.status_code, 200, url)
        return response, response.context['page']

    def test_default_page_size_is_10_on_every_list(self):
        for name, url in self._lists().items():
            _, page = self._page(url)
            self.assertEqual(page.paginator.per_page, 10, name)
            self.assertEqual(len(page.object_list), 10, name)
            self.assertGreaterEqual(page.paginator.count, self.N, name)

    def test_page_size_choices_50_and_100(self):
        for name, url in self._lists().items():
            for size in (50, 100):
                _, page = self._page(url, per_page=size)
                self.assertEqual(page.paginator.per_page, size, f'{name} {size}')
                self.assertEqual(len(page.object_list), min(page.paginator.count, size), f'{name} {size}')

    def test_invalid_page_size_falls_back_to_default(self):
        url = reverse('backoffice:module_list')
        for bad in ('25', '0', '-10', 'abc', '1000', ''):
            client = HttpClient(); client.login(username='admin_boss', password='AdminPassword123!')
            page = client.get(url, {'per_page': bad}).context['page']
            self.assertEqual(page.paginator.per_page, 10, repr(bad))

    def test_chosen_size_is_remembered_across_screens(self):
        self._page(reverse('backoffice:module_list'), per_page=50)
        _, page = self._page(reverse('backoffice:order_list'))
        self.assertEqual(page.paginator.per_page, 50)
        self._page(reverse('backoffice:user_list'), per_page=100)
        _, page = self._page(reverse('backoffice:module_list'))
        self.assertEqual(page.paginator.per_page, 100)

    def test_pages_are_stable_and_do_not_overlap(self):
        for name in ('backoffice:module_list', 'backoffice:bundle_list', 'backoffice:category_list', 'backoffice:user_list'):
            url = reverse(name)
            ids = []
            for number in range(1, 7):
                _, page = self._page(url, page=number)
                ids += [o.pk for o in page.object_list]
            self.assertEqual(len(ids), len(set(ids)), name)
            self.assertEqual(len(ids), 60, name)  # 6 pages de 10

    def test_second_page_and_out_of_range_page(self):
        url = reverse('backoffice:order_list')
        _, page = self._page(url, per_page=50, page=2)
        self.assertEqual(len(page.object_list), 10)  # 60 = 50 + 10
        _, last = self._page(url, per_page=50, page=999)
        self.assertEqual(last.number, 2)  # get_page borne à la dernière page
        _, first = self._page(url, page='abc')
        self.assertEqual(first.number, 1)

    def test_filters_survive_page_and_size_links(self):
        response, page = self._page(reverse('backoffice:order_list'), status='completed')
        self.assertEqual(page.paginator.per_page, 10)
        html = response.content.decode()
        self.assertRegex(html, r'href="\?[^"]*status=completed[^"]*page=2')
        self.assertRegex(html, r'href="\?[^"]*status=completed[^"]*per_page=50')

    def test_pagination_bar_is_translated_and_shows_all_choices(self):
        from django.utils import translation
        for lang, label in (('fr', 'Éléments par page'), ('en', 'Items per page'), ('nl', 'Items per pagina')):
            with translation.override(lang):
                url = reverse('backoffice:module_list')
            html = self.client_http.get(url).content.decode()
            self.assertIn(label, html, lang)
            for size in (10, 50, 100):
                self.assertIn(f'per_page={size}', html, f'{lang} {size}')
        with translation.override('en'):
            self.assertContains(self.client_http.get(reverse('backoffice:module_list')), '1–10 of ')
        with translation.override('nl'):
            self.assertContains(self.client_http.get(reverse('backoffice:module_list')), '1–10 van ')

    def test_bar_hidden_when_everything_fits_on_one_page(self):
        Module.objects.exclude(pk=self.module.pk).delete()
        response = self.client_http.get(reverse('backoffice:module_list'))
        self.assertNotContains(response, 'Éléments par page')

    def test_totals_use_the_full_count_not_the_page(self):
        for name in ('backoffice:license_list', 'backoffice:installation_list', 'backoffice:support_subscription_search'):
            html = self.client_http.get(reverse(name)).content.decode()
            self.assertRegex(html, r'leading-none mt-1">60</p>', name)

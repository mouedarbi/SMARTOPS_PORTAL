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
from django.utils import timezone, translation

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

    def test_dashboard_hides_support_ui_when_module_has_no_support_price(self):
        """Aucun badge/bouton support n'apparaît pour un module sans support_annual_price."""
        from catalog.models import Category, Module
        from licensing.models import License
        from decimal import Decimal

        cat = Category.objects.create(name='Sans Support', slug='sans-support')
        mod = Module.objects.create(name='Module Sans Support', slug='module-sans-support-dash',
                                     price=Decimal('19.00'), category=cat, is_active=True)
        License.objects.create(user=self.user, module=mod, is_active=True, max_activations=1)

        self.client.force_login(self.user)
        response = self.client.get(reverse('users:dashboard'))
        self.assertNotContains(response, "Souscrire au support")
        self.assertNotContains(response, "Support Premium")

    def test_dashboard_shows_subscribe_button_without_active_subscription(self):
        """Un module avec support_annual_price sans abonnement valide affiche le bouton de souscription."""
        from catalog.models import Category, Module
        from licensing.models import License
        from decimal import Decimal

        cat = Category.objects.create(name='Avec Support', slug='avec-support-1')
        mod = Module.objects.create(name='Module Avec Support', slug='module-avec-support-dash',
                                     price=Decimal('99.00'), support_annual_price=Decimal('29.00'),
                                     category=cat, is_active=True)
        License.objects.create(user=self.user, module=mod, is_active=True, max_activations=1)

        self.client.force_login(self.user)
        response = self.client.get(reverse('users:dashboard'))
        self.assertContains(response, "Souscrire au support")
        self.assertNotContains(response, "Support Premium")

    def test_dashboard_shows_premium_badge_with_active_subscription(self):
        """Un abonnement support valide affiche le badge avec la date d'expiration, pas le bouton."""
        from catalog.models import Category, Module
        from licensing.models import License, SupportSubscription
        from decimal import Decimal

        cat = Category.objects.create(name='Avec Support', slug='avec-support-2')
        mod = Module.objects.create(name='Module Avec Support Actif', slug='module-avec-support-actif',
                                     price=Decimal('99.00'), support_annual_price=Decimal('29.00'),
                                     category=cat, is_active=True)
        License.objects.create(user=self.user, module=mod, is_active=True, max_activations=1)
        SupportSubscription.objects.create(
            user=self.user, module=mod,
            expires_at=timezone.now() + timezone.timedelta(days=200),
            amount_paid=Decimal('29.00')
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('users:dashboard'))
        self.assertContains(response, "Support Premium")
        self.assertNotContains(response, "Souscrire au support")

    def test_dashboard_shows_subscribe_button_when_subscription_expired(self):
        """Un abonnement expiré réaffiche le bouton de souscription (pas juste l'existence d'une ligne)."""
        from catalog.models import Category, Module
        from licensing.models import License, SupportSubscription
        from decimal import Decimal

        cat = Category.objects.create(name='Avec Support', slug='avec-support-3')
        mod = Module.objects.create(name='Module Avec Support Expiré', slug='module-avec-support-expire',
                                     price=Decimal('99.00'), support_annual_price=Decimal('29.00'),
                                     category=cat, is_active=True)
        License.objects.create(user=self.user, module=mod, is_active=True, max_activations=1)
        SupportSubscription.objects.create(
            user=self.user, module=mod,
            expires_at=timezone.now() - timezone.timedelta(days=5),
            amount_paid=Decimal('29.00')
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('users:dashboard'))
        self.assertContains(response, "Souscrire au support")
        self.assertNotContains(response, "Support Premium")




@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DeleteAccountHoldingsTests(TestCase):
    """La suppression n'est jamais refusée. Un support encore dans son délai légal de
    rétractation (14 jours, Art. VI.51 CDE) donne lieu à un remboursement calculé
    automatiquement et consigné sur la commande pour un traitement manuel par l'équipe."""

    def setUp(self):
        from decimal import Decimal
        from datetime import timedelta
        from catalog.models import Category, Module
        from licensing.models import License, SupportSubscription
        from payments.models import Order, OrderItem
        self.addCleanup(translation.activate, 'fr')
        self.user = User.objects.create_user('alice', 'alice@example.org', 'Password123!')
        category = Category.objects.create(name='Analytics', slug='analytics')
        self.module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('10.00'), category=category, is_active=True)
        self.old_module = Module.objects.create(name='Module RH', slug='module-rh', price=Decimal('10.00'), category=category, is_active=True)
        self.expired_module = Module.objects.create(name='Module Stock', slug='module-stock', price=Decimal('10.00'), category=category, is_active=True)
        self.license = License.objects.create(user=self.user, module=self.module)

        # Support payé il y a 5 jours : encore dans le délai légal de rétractation -> remboursement dû.
        SupportSubscription.objects.create(
            user=self.user, module=self.module, expires_at=timezone.now() + timedelta(days=360), amount_paid=Decimal('50.00'))
        self.recent_order = self._support_order(self.module, Decimal('50.00'), days_ago=5)

        # Support payé il y a 100 jours : délai dépassé -> rien n'est dû.
        SupportSubscription.objects.create(
            user=self.user, module=self.old_module, expires_at=timezone.now() + timedelta(days=265), amount_paid=Decimal('49.00'))
        self.old_order = self._support_order(self.old_module, Decimal('49.00'), days_ago=100)

        # Support déjà expiré : ne doit même plus apparaître.
        SupportSubscription.objects.create(
            user=self.user, module=self.expired_module, expires_at=timezone.now() - timedelta(days=1), amount_paid=Decimal('49.00'))

        self.client.login(username='alice', password='Password123!')
        self.url = '/fr/accounts/delete-account/'

    def _support_order(self, module, amount, days_ago):
        from datetime import timedelta
        from payments.models import Order, OrderItem
        order = Order.objects.create(user=self.user, status='completed', total_amount=amount,
                                      stripe_payment_intent_id=f'pi_{module.slug}')
        OrderItem.objects.create(order=order, module=module, price_at_purchase=amount, product_type='support')
        Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(days=days_ago))
        order.refresh_from_db()
        return order

    def post(self):
        return self.client.post(self.url, {'confirmation': 'SUPPRIMER'})

    def test_page_shows_refund_due_within_the_withdrawal_period(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Module BI')
        self.assertContains(response, str(self.license.license_key))
        self.assertContains(response, 'délai légal de rétractation')
        self.assertContains(response, '49,32')  # 50€ - 5/365 consommés, formaté en fr

    def test_page_shows_no_refund_past_the_withdrawal_period(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Module RH')
        self.assertContains(response, 'sans remboursement')

    def test_expired_support_without_licence_is_not_listed(self):
        self.assertNotContains(self.client.get(self.url), 'Module Stock')

    def test_no_confirmation_checkbox_is_required_deletion_is_never_blocked(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'accept_no_refund')
        self.assertEqual(self.post().status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)

    def test_deletion_keeps_licences_active(self):
        from licensing.models import License
        self.post()
        self.assertTrue(License.objects.filter(pk=self.license.pk, is_active=True).exists())

    def test_deletion_records_the_refund_due_on_the_order_for_manual_processing(self):
        self.post()
        self.recent_order.refresh_from_db()
        self.assertIsNotNone(self.recent_order.refund_due_amount)
        self.assertAlmostEqual(float(self.recent_order.refund_due_amount), 49.32, delta=0.05)

    def test_deletion_records_nothing_for_a_support_past_the_withdrawal_period(self):
        self.post()
        self.old_order.refresh_from_db()
        self.assertIsNone(self.old_order.refund_due_amount)

    def test_wrong_typed_word_blocks_and_records_no_refund(self):
        response = self.client.post(self.url, {'confirmation': 'oui'})
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_deleted)
        self.recent_order.refresh_from_db()
        self.assertIsNone(self.recent_order.refund_due_amount)

    def test_account_without_holdings_deletes_cleanly(self):
        bob = User.objects.create_user('bob', 'bob@example.org', 'Password123!')
        self.client.logout()
        self.client.login(username='bob', password='Password123!')
        self.assertNotContains(self.client.get(self.url), 'délai légal de rétractation')
        self.assertEqual(self.post().status_code, 302)
        bob.refresh_from_db()
        self.assertTrue(bob.is_deleted)

    def test_page_is_translated(self):
        for lang, text in (('en', 'Your current products and services'), ('nl', 'Uw huidige producten en diensten')):
            self.assertContains(self.client.get(f'/{lang}/accounts/delete-account/'), text)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LicenseRefundOnDeletionTests(TestCase):
    """Suppression du compte : remboursement des licences dans les 14 jours suivant la commande.

    Licence jamais activée : remboursée (geste commercial). Activée avec renonciation : rien.
    Activée sans renonciation enregistrée : remboursée (droit de rétractation). Passé 14 jours :
    rien. Une licence remboursée est désactivée dans la même transaction."""

    def setUp(self):
        from decimal import Decimal
        from catalog.models import Category, Module, ModuleBundle
        self.addCleanup(translation.activate, 'fr')
        self.user = User.objects.create_user('lea', 'lea@example.org', 'Password123!', first_name='Léa', last_name='Martin')
        category = Category.objects.create(name='Analytics', slug='analytics')
        self.module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('100.00'), category=category)
        self.other = Module.objects.create(name='Module RH', slug='module-rh', price=Decimal('80.00'), category=category)
        self.bundle = ModuleBundle.objects.create(name='Pack Gestion', slug='pack-gestion', short_description='-',
                                                  description='-')
        self.bundle.modules.set([self.module, self.other])
        self.client.login(username='lea@example.org', password='Password123!')
        self.url = '/fr/accounts/delete-account/'

    def _buy(self, days_ago, waiver=True, bundle=False, price='100.00', activated=()):
        """Commande (module seul ou pack) passée il y a `days_ago` jours, puis ses licences."""
        from datetime import timedelta
        from decimal import Decimal
        from payments.models import Order, OrderItem
        from licensing.models import License
        created = timezone.now() - timedelta(days=days_ago)
        order = Order.objects.create(user=self.user, status='completed', total_amount=Decimal(price),
                                     withdrawal_waiver_accepted_at=created if waiver else None)
        Order.objects.filter(pk=order.pk).update(created_at=created)
        order.refresh_from_db()
        item = OrderItem.objects.create(order=order, price_at_purchase=Decimal(price),
                                        **({'bundle': self.bundle} if bundle else {'module': self.module}))
        modules = [self.module, self.other] if bundle else [self.module]
        licenses = [License.objects.create(user=self.user, module=m, activation_count=1 if m in activated else 0)
                    for m in modules]
        return order, item, licenses

    def post(self):
        return self.client.post(self.url, {'confirmation': 'SUPPRIMER'}, follow=True)

    def assertNoRefund(self, order, licenses):
        self.post()
        order.refresh_from_db()
        self.assertIsNone(order.refund_due_amount)
        self.assertEqual(order.status, 'completed')
        for lic in licenses:
            lic.refresh_from_db()
            self.assertTrue(lic.is_active)

    def test_never_activated_licence_within_14_days_is_fully_refunded_and_deactivated(self):
        from decimal import Decimal
        order, item, (lic,) = self._buy(days_ago=3)
        self.post()
        order.refresh_from_db(); item.refresh_from_db(); lic.refresh_from_db()
        self.assertEqual(order.refund_due_amount, Decimal('100.00'))
        self.assertEqual(order.status, 'refund_pending')
        self.assertEqual(item.refund_due_amount, Decimal('100.00'))
        self.assertEqual(item.refund_reason, 'unused_license')
        self.assertFalse(lic.is_active)

    def test_licence_bound_to_an_installation_counts_as_activated(self):
        from licensing.models import Installation
        import uuid
        order, _, (lic,) = self._buy(days_ago=3)
        lic.installation = Installation.objects.create(installation_uuid=uuid.uuid4())
        lic.save()
        self.assertNoRefund(order, [lic])

    def test_activated_licence_with_waiver_is_not_refunded(self):
        order, _, licenses = self._buy(days_ago=3, activated=[self.module])
        self.assertNoRefund(order, licenses)

    def test_activated_licence_without_waiver_is_refunded_under_the_withdrawal_right(self):
        from decimal import Decimal
        order, item, (lic,) = self._buy(days_ago=3, waiver=False, activated=[self.module])
        self.post()
        item.refresh_from_db(); lic.refresh_from_db()
        self.assertEqual(item.refund_due_amount, Decimal('100.00'))
        self.assertEqual(item.refund_reason, 'no_waiver')
        self.assertFalse(lic.is_active)

    def test_never_activated_licence_after_14_days_is_not_refunded(self):
        order, _, licenses = self._buy(days_ago=15)
        self.assertNoRefund(order, licenses)

    def test_bundle_with_one_activated_licence_is_not_refunded(self):
        order, _, licenses = self._buy(days_ago=3, bundle=True, price='150.00', activated=[self.other])
        self.assertNoRefund(order, licenses)

    def test_bundle_without_any_activation_is_refunded_at_the_bundle_price(self):
        from decimal import Decimal
        order, item, licenses = self._buy(days_ago=3, bundle=True, price='150.00')
        self.post()
        order.refresh_from_db(); item.refresh_from_db()
        self.assertEqual(order.refund_due_amount, Decimal('150.00'))
        self.assertEqual(item.refund_reason, 'unused_license')
        for lic in licenses:
            lic.refresh_from_db()
            self.assertFalse(lic.is_active)

    def test_support_and_licence_on_the_same_order_add_up(self):
        from datetime import timedelta
        from decimal import Decimal
        from licensing.models import SupportSubscription
        from payments.models import OrderItem
        order, item, _ = self._buy(days_ago=3)
        support = OrderItem.objects.create(order=order, module=self.module, price_at_purchase=Decimal('50.00'),
                                           product_type='support')
        SupportSubscription.objects.create(user=self.user, module=self.module, amount_paid=Decimal('50.00'),
                                           expires_at=timezone.now() + timedelta(days=362))
        self.post()
        order.refresh_from_db(); support.refresh_from_db()
        self.assertEqual(support.refund_reason, 'withdrawal_support')
        self.assertEqual(support.refund_due_amount, Decimal('49.59'))  # 50 € - 3/365 consommés
        self.assertEqual(order.refund_due_amount, Decimal('149.59'))

    def test_confirmation_page_lists_refundable_and_non_refundable_licences(self):
        self._buy(days_ago=3)
        old_order, _, _ = self._buy(days_ago=20)
        response = self.client.get(self.url)
        self.assertContains(response, 'licence jamais activée, dans le délai de 14 jours')
        self.assertContains(response, 'Licence non remboursable')
        self.assertContains(response, '100,00')

    def success_message(self):
        from django.contrib.messages import get_messages
        response = self.client.post(self.url, {'confirmation': 'SUPPRIMER'})
        return ' '.join(str(m) for m in get_messages(response.wsgi_request))

    def test_success_message_details_support_and_licences(self):
        self._buy(days_ago=3)
        message = self.success_message()
        self.assertIn('0,00 € pour le support', message)
        self.assertIn('100,00 € pour les licences', message)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SoftDeleteTests(TestCase):
    """Suppression par le client : le compte est désactivé et gelé, ses données personnelles restent
    intactes pendant le délai de grâce ; l'anonymisation est faite plus tard par la commande planifiée."""

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        self.user = User.objects.create_user('paul', 'paul@example.org', 'Password123!', first_name='Paul', last_name='Durand')
        self.client.login(username='paul@example.org', password='Password123!')
        self.client.post('/fr/accounts/delete-account/', {'confirmation': 'SUPPRIMER'})
        self.client.logout()
        self.user.refresh_from_db()

    def test_account_is_deactivated_but_personal_data_is_kept(self):
        self.assertTrue(self.user.is_deleted)
        self.assertIsNotNone(self.user.deleted_at)
        self.assertFalse(self.user.is_active)
        self.assertEqual((self.user.username, self.user.email, self.user.first_name, self.user.last_name),
                         ('paul', 'paul@example.org', 'Paul', 'Durand'))
        self.assertTrue(self.user.check_password('Password123!'))
        self.assertFalse(self.user.is_anonymized)

    def test_login_is_refused(self):
        self.assertFalse(self.client.login(username='paul@example.org', password='Password123!'))
        self.client.post(reverse('account_login'), {'login': 'paul@example.org', 'password': 'Password123!'})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_no_email_is_sent_to_a_frozen_account(self):
        from django.core import mail
        self.client.post(reverse('account_reset_password'), {'email': 'paul@example.org'})
        self.assertEqual(len(mail.outbox), 0)

    def test_success_message_announces_the_deferred_anonymization(self):
        from django.contrib.messages import get_messages
        other = User.objects.create_user('zoe', 'zoe@example.org', 'Password123!')
        self.client.login(username='zoe@example.org', password='Password123!')
        response = self.client.post('/fr/accounts/delete-account/', {'confirmation': 'SUPPRIMER'})
        text = ' '.join(str(m) for m in get_messages(response.wsgi_request))
        self.assertIn('Votre compte a été désactivé', text)
        self.assertIn('anonymisées dans un délai de 30 jours', text)

    def test_anonymize_keeps_the_date_of_the_deletion_request(self):
        requested_at = self.user.deleted_at
        self.user.anonymize()
        self.user.refresh_from_db()
        self.assertEqual(self.user.deleted_at, requested_at)
        self.assertTrue(self.user.is_anonymized)

    def test_reviews_are_hidden_during_the_grace_period_then_shown_anonymized(self):
        from decimal import Decimal
        from catalog.models import Category, Module, Review
        category = Category.objects.create(name='Analytics', slug='analytics')
        module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('10.00'), category=category, is_active=True)
        Review.objects.create(module=module, user=self.user, rating=5, comment='Excellent module', is_approved=True)
        url = reverse('catalog:module_detail', kwargs={'slug': module.slug})
        self.assertNotContains(self.client.get(url), 'Excellent module')
        self.user.anonymize()
        response = self.client.get(url)
        self.assertContains(response, 'Excellent module')
        self.assertNotContains(response, 'paul')


class LanguagePreferenceTests(TestCase):
    """Annexe D : users_user.language_preference = code langue (fr, en, nl)."""

    def test_language_preference_offers_the_three_site_languages(self):
        field = User._meta.get_field('language_preference')
        self.assertEqual([code for code, _ in field.choices], ['fr', 'en', 'nl'])

    def test_dutch_preference_is_valid(self):
        user = User(username='nl_user', email='nl@example.org', language_preference='nl')
        user.set_password('x')
        user.full_clean()


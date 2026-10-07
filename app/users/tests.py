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
from django.conf import settings
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

    def test_anonymize_removes_the_email_copy_kept_by_allauth(self):
        from allauth.account.models import EmailAddress
        user = User.objects.create_user('gdpr_mail', 'gdpr_mail@example.com', 'password123')
        EmailAddress.objects.create(user=user, email='gdpr_mail@example.com', primary=True, verified=True)
        user.soft_delete()
        self.assertTrue(EmailAddress.objects.filter(email='gdpr_mail@example.com').exists())  # délai de grâce
        user.anonymize()
        self.assertFalse(EmailAddress.objects.filter(user=user).exists())
        self.assertFalse(EmailAddress.objects.filter(email='gdpr_mail@example.com').exists())

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
        mail.outbox = []  # le récapitulatif de suppression, envoyé par setUp
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


class AnonymizeDeletedAccountsCommandTests(TestCase):
    """Commande planifiée : anonymise les comptes supprimés depuis plus de ACCOUNT_ANONYMIZATION_DELAY_DAYS
    jours (30 par défaut), en conservant la date de la demande ; idempotente ; --dry-run ne modifie rien."""

    def setUp(self):
        self.recent = self._deleted('recent', days_ago=29)
        self.old = self._deleted('old', days_ago=31)
        self.active = User.objects.create_user('active', 'active@example.org', 'Password123!')

    def _deleted(self, name, days_ago):
        from datetime import timedelta
        user = User.objects.create_user(name, f'{name}@example.org', 'Password123!', first_name=name.title())
        user.soft_delete()
        User.objects.filter(pk=user.pk).update(deleted_at=timezone.now() - timedelta(days=days_ago))
        user.refresh_from_db()
        return user

    def run_command(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('anonymize_deleted_accounts', *args, stdout=out)
        return out.getvalue()

    def snapshot(self):
        return list(User.objects.order_by('pk').values_list('username', 'email', 'first_name', 'deleted_at', 'password'))

    def test_account_deleted_29_days_ago_is_left_untouched(self):
        self.run_command()
        self.recent.refresh_from_db()
        self.assertEqual((self.recent.email, self.recent.first_name), ('recent@example.org', 'Recent'))

    def test_account_deleted_31_days_ago_is_anonymized_and_keeps_its_deletion_date(self):
        requested_at = self.old.deleted_at
        output = self.run_command()
        self.old.refresh_from_db()
        self.assertTrue(self.old.is_anonymized)
        self.assertEqual(self.old.first_name, '')
        self.assertFalse(self.old.has_usable_password())
        self.assertEqual(self.old.deleted_at, requested_at)
        self.assertIn('1 compte(s) anonymisé(s)', output)

    def test_audit_log_has_one_line_per_account_without_personal_data(self):
        with self.assertLogs('audit', level='INFO') as logs:
            self.run_command()
        self.assertEqual(len(logs.output), 1)
        self.assertIn(f'User ID {self.old.pk} anonymized', logs.output[0])
        self.assertNotIn('old', logs.output[0].replace(f'User ID {self.old.pk}', ''))

    def test_running_twice_changes_nothing(self):
        self.run_command()
        before = self.snapshot()
        output = self.run_command()
        self.assertEqual(self.snapshot(), before)
        self.assertIn('0 compte(s)', output)

    def test_dry_run_lists_without_modifying(self):
        before = self.snapshot()
        with self.assertNoLogs('audit', level='INFO'):
            output = self.run_command('--dry-run')
        self.assertEqual(self.snapshot(), before)
        self.assertIn(f'Compte ID {self.old.pk}', output)
        self.assertNotIn(f'Compte ID {self.recent.pk}', output)
        self.assertNotIn('old@example.org', output)

    def test_orders_and_licences_are_kept(self):
        from decimal import Decimal
        from catalog.models import Category, Module
        from licensing.models import License
        from payments.models import Order
        module = Module.objects.create(name='Module BI', slug='module-bi', price=Decimal('10.00'),
                                       category=Category.objects.create(name='BI', slug='bi'))
        order = Order.objects.create(user=self.old, status='completed', total_amount=Decimal('10.00'))
        licence = License.objects.create(user=self.old, module=module)
        self.run_command()
        self.assertTrue(Order.objects.filter(pk=order.pk, user=self.old, status='completed').exists())
        self.assertTrue(License.objects.filter(pk=licence.pk, user=self.old, is_active=True).exists())

    @override_settings(ACCOUNT_ANONYMIZATION_DELAY_DAYS=7)
    def test_delay_comes_from_the_setting(self):
        self.run_command()
        self.recent.refresh_from_db()
        self.assertTrue(self.recent.is_anonymized)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountTypeAndBillingProfileTests(TestCase):
    """Particulier ou professionnel : choisi à l'inscription, jamais converti ensuite. Un compte
    professionnel (entreprise belge) a des coordonnées de facturation, modifiables par lui seul."""

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')

    def signup(self, **extra):
        data = {'username': 'pme_dupont', 'email': 'pme@example.org',
                'password1': 'MotDePasse!2026', 'password2': 'MotDePasse!2026', **extra}
        return self.client.post('/fr/accounts/signup/', data)

    def pro_fields(self, **overrides):
        return {'account_type': 'professional', 'company_name': 'Dupont Maintenance SRL',
                'vat_number': 'be 0123.456.749', 'street': 'Rue de la Loi 1', 'postal_code': '1000',
                'city': 'Bruxelles', **overrides}

    def test_signup_without_choice_creates_an_individual_account(self):
        self.signup()
        user = User.objects.get(username='pme_dupont')
        self.assertEqual(user.account_type, 'individual')
        self.assertFalse(hasattr(user, 'billing_profile') and user.billing_profile)

    def test_professional_signup_records_the_company(self):
        self.signup(**self.pro_fields())
        user = User.objects.get(username='pme_dupont')
        self.assertTrue(user.is_professional)
        self.assertEqual(user.billing_profile.company_name, 'Dupont Maintenance SRL')
        self.assertEqual(user.billing_profile.vat_number, 'be 0123.456.749')

    def test_vat_number_is_free_text(self):
        self.signup(**self.pro_fields(vat_number='BE 0123.456.748 (clé fausse)'))
        user = User.objects.get(username='pme_dupont')
        self.assertEqual(user.billing_profile.vat_number, 'BE 0123.456.748 (clé fausse)')

    def test_professional_signup_requires_the_company_details(self):
        response = self.signup(**self.pro_fields(city='', vat_number=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='pme_dupont').exists())
        self.assertContains(response, 'obligatoire pour un compte professionnel')

    def test_professional_can_edit_billing_details_but_not_the_account_type(self):
        self.signup(**self.pro_fields())
        response = self.client.post('/fr/accounts/profile/billing/', {
            'company_name': 'Dupont & Fils SRL', 'vat_number': 'BE0412345614', 'street': 'Rue Neuve 2',
            'postal_code': '4000', 'city': 'Liège', 'account_type': 'individual'})
        self.assertRedirects(response, '/fr/accounts/profile/', fetch_redirect_response=False)
        user = User.objects.get(username='pme_dupont')
        self.assertEqual(user.billing_profile.company_name, 'Dupont & Fils SRL')
        self.assertTrue(user.is_professional)
        self.assertContains(self.client.get('/fr/accounts/profile/'), 'Dupont &amp; Fils SRL')
        self.assertContains(self.client.get('/fr/accounts/dashboard/'), 'Dupont &amp; Fils SRL')

    def test_individual_has_no_billing_page(self):
        self.signup()
        self.assertEqual(self.client.get('/fr/accounts/profile/billing/').status_code, 404)

    def test_anonymization_erases_the_company_details(self):
        from users.models import BillingProfile
        self.signup(**self.pro_fields())
        user = User.objects.get(username='pme_dupont')
        user.anonymize()
        self.assertFalse(BillingProfile.objects.filter(user=user).exists())


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DemoClientsTests(TestCase):
    """Clients fictifs : adresses Gmail en plus addressing (opensmartops+userN@gmail.com) et 70 % de
    comptes professionnels avec coordonnées d'entreprise fictives. Les autres comptes ne sont jamais touchés."""

    def setUp(self):
        from allauth.account.models import EmailAddress
        self.fictitious = [User.objects.create_user(f'client{i}', f'client{i}@example.be', 'x',
                                                    first_name='Anne', last_name='Peeters') for i in range(10)]
        EmailAddress.objects.create(user=self.fictitious[0], email='client0@example.be', primary=True, verified=False)
        self.kept = [
            User.objects.create_superuser('admin', 'admin@example.be', 'x'),
            User.objects.create_user('perso', 'perso@gmail.com', 'x'),
            User.objects.create_user('tfe_demo_client', 'tfe@opensmartops.org', 'x'),
        ]
        gone = User.objects.create_user('parti', 'parti@example.be', 'x')
        gone.soft_delete()
        self.kept.append(gone)
        self.snapshot = {u.pk: (u.email, u.account_type) for u in self.kept}

    def run_command(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('prepare_demo_clients', *args, stdout=out)
        return out.getvalue()

    def test_fictitious_clients_get_plus_addresses_and_a_70_30_split(self):
        from allauth.account.models import EmailAddress
        self.run_command()
        users = User.objects.filter(pk__in=[u.pk for u in self.fictitious]).order_by('pk')
        self.assertEqual([u.email for u in users], [f'opensmartops+user{n}@gmail.com' for n in range(1, 11)])
        pros = [u for u in users if u.is_professional]
        self.assertEqual(len(pros), 7)
        for user in pros:
            self.assertRegex(user.billing_profile.vat_number, r"^BE[01][0-9]{9}$")
        self.assertEqual(EmailAddress.objects.get(user=self.fictitious[0]).email, 'opensmartops+user1@gmail.com')

    def test_other_accounts_are_never_touched(self):
        self.run_command()
        for user in self.kept:
            user.refresh_from_db()
            self.assertEqual((user.email, user.account_type), self.snapshot[user.pk])

    def test_running_twice_changes_nothing_and_dry_run_changes_nothing(self):
        before = list(User.objects.order_by('pk').values_list('email', 'account_type'))
        output = self.run_command('--dry-run')
        self.assertIn('10 compte(s) à convertir : 7 professionnel(s), 3 particulier(s)', output)
        self.assertEqual(list(User.objects.order_by('pk').values_list('email', 'account_type')), before)
        self.run_command()
        after = list(User.objects.order_by('pk').values_list('email', 'account_type'))
        self.assertIn('0 compte(s) converti(s)', self.run_command())
        self.assertEqual(list(User.objects.order_by('pk').values_list('email', 'account_type')), after)

    @override_settings(DEBUG=True)
    def test_populate_script_creates_plus_addresses_and_70_percent_professionals(self):
        import os
        from unittest import mock
        from users import populate_portal_clients
        with mock.patch.dict(os.environ, {'PORTAL_ADMIN_PASSWORD': 'x'}):
            populate_portal_clients.run()
        clients = User.objects.filter(is_superuser=False)
        self.assertEqual(clients.count(), 100)
        self.assertEqual(clients.filter(account_type='professional', billing_profile__isnull=False).count(), 70)
        self.assertFalse(clients.exclude(email__regex=r'^opensmartops\+user\d+@gmail\.com$').exists())


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ProfessionalAccountRefundTests(LicenseRefundOnDeletionTests):
    """Compte professionnel : pas de droit de rétractation ni de geste commercial, donc aucun
    remboursement à la suppression du compte, même pour une licence jamais activée."""

    def setUp(self):
        super().setUp()
        User.objects.filter(pk=self.user.pk).update(account_type='professional')

    def test_professional_gets_no_refund_for_licences_or_support(self):
        from datetime import timedelta
        from licensing.models import SupportSubscription
        from payments.models import OrderItem
        from decimal import Decimal
        order, _, licenses = self._buy(days_ago=3, waiver=False)
        OrderItem.objects.create(order=order, module=self.module, price_at_purchase=Decimal('50.00'), product_type='support')
        SupportSubscription.objects.create(user=self.user, module=self.module, amount_paid=Decimal('50.00'),
                                           expires_at=timezone.now() + timedelta(days=362))
        page = self.client.get(self.url)
        self.assertContains(page, 'Licence non remboursable (compte professionnel)')
        self.assertContains(page, 'pas de droit de rétractation')
        self.assertNoRefund(order, licenses)

    # Les cas « particulier » hérités ne s'appliquent pas à un compte professionnel.
    test_never_activated_licence_within_14_days_is_fully_refunded_and_deactivated = None
    test_activated_licence_without_waiver_is_refunded_under_the_withdrawal_right = None
    test_bundle_without_any_activation_is_refunded_at_the_bundle_price = None
    test_support_and_licence_on_the_same_order_add_up = None
    test_confirmation_page_lists_refundable_and_non_refundable_licences = None
    test_success_message_details_support_and_licences = None


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountDeletionEmailTests(TestCase):
    """Après la suppression du compte, le client reçoit dans sa langue le récapitulatif de ce
    qu'elle a entraîné, les clés de ses licences et le remboursement éventuellement dû."""

    setUp = LicenseRefundOnDeletionTests.setUp
    _buy = LicenseRefundOnDeletionTests._buy
    post = LicenseRefundOnDeletionTests.post

    def message(self):
        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['lea@example.org'])
        return mail.outbox[0]

    def test_refunded_licence_is_listed_with_its_key_and_the_total(self):
        _, _, (lic,) = self._buy(days_ago=3)
        self.post()
        message = self.message()
        self.assertIn('Suppression de votre compte SMARTOPS', message.subject)
        self.assertIn(f'Clé de licence : {lic.license_key}', message.body)
        self.assertIn('Raison : licence jamais activée', message.body)
        self.assertIn('Cette licence a été désactivée.', message.body)
        self.assertIn('Total qui vous sera remboursé : 100,00 €.', message.body)
        self.assertIn('anonymisés dans un délai de 30 jours', message.body)
        self.assertNotIn('/accounts/dashboard/', message.alternatives[0][0])

    def test_kept_licence_key_is_sent_without_refund(self):
        _, _, (lic,) = self._buy(days_ago=3, activated=(self.module,))
        self.post()
        message = self.message()
        self.assertIn(str(lic.license_key), message.body)
        self.assertIn('Licence non remboursable (déjà activée', message.body)
        self.assertNotIn('Total qui vous sera remboursé', message.body)

    def test_account_without_holdings_still_gets_the_summary(self):
        self.post()
        message = self.message()
        self.assertIn('Votre compte est désactivé', message.body)
        self.assertNotIn('Clé de licence', message.body)

    def test_email_uses_the_customer_language(self):
        User.objects.filter(pk=self.user.pk).update(language_preference='nl')
        self._buy(days_ago=3)
        self.post()
        message = self.message()
        self.assertIn('Verwijdering van uw SMARTOPS-account', message.subject)
        self.assertIn('Deze licentie is gedeactiveerd.', message.body)

    def test_professional_summary_mentions_billing_details_and_no_refund(self):
        User.objects.filter(pk=self.user.pk).update(account_type='professional')
        self._buy(days_ago=3)
        self.post()
        message = self.message()
        self.assertIn('Vos coordonnées de facturation seront effacées', message.body)
        self.assertIn('Licence non remboursable (compte professionnel).', message.body)

    def test_email_failure_does_not_block_the_deletion(self):
        from unittest.mock import patch
        with patch('users.emails.EmailMultiAlternatives.send', side_effect=OSError('SMTP indisponible')), \
                self.assertLogs('audit', level='ERROR'):
            self.post()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)


class LanguagePreferenceTests(TestCase):
    """Annexe D : users_user.language_preference = code langue (fr, en, nl)."""

    def test_language_preference_offers_the_three_site_languages(self):
        field = User._meta.get_field('language_preference')
        self.assertEqual([code for code, _ in field.choices], ['fr', 'en', 'nl'])

    def test_dutch_preference_is_valid(self):
        user = User(username='nl_user', email='nl@example.org', language_preference='nl')
        user.set_password('x')
        user.full_clean()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LanguagePreferenceEditTests(TestCase):
    """Le client choisit la langue de ses e-mails : sélecteur du site ou page profil."""

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        self.user = User.objects.create_user('client', 'client@example.org', 'Password123!')
        self.client.login(username='client@example.org', password='Password123!')

    def test_site_language_switch_saves_the_preference(self):
        response = self.client.post(reverse('set_language'), {'language': 'nl', 'next': '/accounts/profile/'})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.language_preference, 'nl')

    def test_site_language_switch_ignores_unknown_languages(self):
        self.client.post(reverse('set_language'), {'language': 'de', 'next': '/'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.language_preference, 'fr')

    def test_site_language_switch_works_for_visitors(self):
        self.client.logout()
        response = self.client.post(reverse('set_language'), {'language': 'en', 'next': '/'})
        self.assertEqual(response.status_code, 302)

    def test_profile_form_saves_the_preference(self):
        response = self.client.post('/fr/accounts/profile/language/', {'language_preference': 'en'})
        self.assertRedirects(response, '/fr/accounts/profile/', fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.language_preference, 'en')

    def test_profile_shows_the_current_preference(self):
        User.objects.filter(pk=self.user.pk).update(language_preference='nl')
        response = self.client.get('/fr/accounts/profile/')
        self.assertContains(response, '<option value="nl" selected>')



class UnknownAccountPasswordResetTestCase(TestCase):
    """Mot de passe oublié pour une adresse sans compte : aucun e-mail n'est envoyé."""

    def test_no_email_is_sent_to_an_unknown_address(self):
        from django.core import mail
        response = self.client.post(reverse('account_reset_password'), {'email': 'inconnu@example.org'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_subject_carries_the_smartops_prefix(self):
        from django.core import mail
        User.objects.create_user('known', 'known@example.org', 'Password123!')
        self.client.post(reverse('account_reset_password'), {'email': 'known@example.org'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].subject.startswith('[SMARTOPS] '))
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

    def test_reset_email_is_sent_in_the_language_of_the_page(self):
        from django.core import mail
        self.addCleanup(translation.activate, 'fr')
        User.objects.create_user('known', 'known@example.org', 'Password123!')
        for lang, greeting in (('fr', "Bonjour, c'est SMARTOPS"), ('en', 'Hello from SMARTOPS'),
                               ('nl', 'Hallo van SMARTOPS')):
            mail.outbox = []
            with translation.override(lang):
                url = reverse('account_reset_password')
            self.client.post(url, {'email': 'known@example.org'})
            self.assertIn(greeting, mail.outbox[0].body, lang)
            self.assertIn(f'/{lang}/accounts/password/reset/key/', mail.outbox[0].body, lang)
            self.assertNotIn('example.com', mail.outbox[0].body, lang)

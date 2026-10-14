"""
Fichier : tests_prices.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Affichage des prix : TTC pour un particulier ou un visiteur, HTVA puis TTC pour un professionnel (#77).
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from catalog.models import Category, Module, ModuleBundle
from payments.invoicing import issue_invoice
from payments.models import Order, OrderItem
from users.models import BillingProfile

User = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PriceDisplayTestCase(TestCase):
    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        category = Category.objects.create(name='IoT', slug='iot')
        self.module = Module.objects.create(name='Module Capteur', slug='module-capteur', category=category,
                                            short_description='-', description='-', price=Decimal('149.00'))
        self.bundle = ModuleBundle.objects.create(name='Pack Capteurs', slug='pack-capteurs', short_description='-',
                                                  description='-', discount_value=Decimal('10'))
        self.bundle.modules.add(self.module)
        self.individual = User.objects.create_user('perso', 'perso@example.org', 'Password123!')
        self.pro = User.objects.create_user('pme', 'pme@example.org', 'Password123!')
        User.objects.filter(pk=self.pro.pk).update(account_type='professional')
        self.pro.refresh_from_db()
        BillingProfile.objects.create(user=self.pro, company_name='Dupont Maintenance SRL', vat_number='BE0123456749',
                                      street='Rue de la Loi 1', postal_code='1000', city='Bruxelles')

    def _pages(self):
        return [reverse('core:home'), reverse('catalog:module_list'),
                reverse('catalog:module_detail', args=[self.module.slug]),
                reverse('catalog:bundle_detail', args=[self.bundle.slug])]

    def test_visitor_and_individual_see_prices_including_vat(self):
        for user in (None, self.individual):
            if user:
                self.client.force_login(user)
            for url in self._pages():
                html = self.client.get(url).content.decode()
                self.assertIn('149,00 €', html, url)
                self.assertIn('TTC', html, url)
                self.assertNotIn('HTVA', html, url)

    def test_professional_sees_price_excluding_vat_then_including_vat(self):
        self.client.force_login(self.pro)
        for url in self._pages():
            html = self.client.get(url).content.decode()
            self.assertIn('123,14 €', html, url)  # 149,00 / 1,21, arrondi comme la facture
            self.assertIn('HTVA', html, url)
            self.assertIn('149,00 € TTC', html, url)
        detail = self.client.get(reverse('catalog:module_detail', args=[self.module.slug])).content.decode()
        self.assertLess(detail.index('123,14 €'), detail.index('149,00 € TTC'))

    def test_labels_are_translated(self):
        self.client.force_login(self.pro)
        for lang, excl, incl in (('en', 'excl. VAT', 'incl. VAT'), ('nl', 'excl. btw', 'incl. btw')):
            with translation.override(lang):
                url = reverse('catalog:module_detail', args=[self.module.slug])
            html = self.client.get(url).content.decode()
            self.assertIn(excl, html, lang)
            self.assertIn(incl, html, lang)

    def _paid_order(self, user, *prices):
        order = Order.objects.create(user=user, status='completed', total_amount=sum(prices, Decimal('0')))
        for price in prices:
            OrderItem.objects.create(order=order, module=self.module, price_at_purchase=price)
        return order

    def test_dashboard_uses_the_invoice_amounts_for_a_professional(self):
        # Deux lignes arrondies une à une : 123,97 + 123,97 = 247,94 € HTVA, alors que 300,00 / 1,21 = 247,93.
        order = self._paid_order(self.pro, Decimal('150.00'), Decimal('150.00'))
        invoice = issue_invoice(order)
        self.assertEqual(invoice.total_excl_vat, Decimal('247.94'))
        self.client.force_login(self.pro)
        html = self.client.get(reverse('users:dashboard')).content.decode()
        self.assertIn('247,94 € HTVA (300,00 € TTC)', html)
        self.assertNotIn('247,93', html)

    def test_dashboard_of_an_individual_shows_prices_including_vat(self):
        self._paid_order(self.individual, Decimal('149.00'))
        self.client.force_login(self.individual)
        html = self.client.get(reverse('users:dashboard')).content.decode()
        self.assertIn('149,00 € TTC', html)
        self.assertNotIn('HTVA', html)

    def test_confirmation_email_of_a_professional_breaks_down_vat(self):
        order = self._paid_order(self.pro, Decimal('149.00'))
        invoice = issue_invoice(order)
        context = {'order': order, 'items': order.items.all(), 'invoice': invoice, 'user': self.pro}
        for template in ('payments/email/order_confirmation_message.txt', 'payments/email/order_confirmation_message.html'):
            text = render_to_string(template, context)
            self.assertIn('123,14 € HTVA (149,00 € TTC)', text, template)
            self.assertIn('dont TVA 21 % : 25,86 €', text, template)

    def test_confirmation_email_of_an_individual_is_unchanged_in_substance(self):
        order = self._paid_order(self.individual, Decimal('149.00'))
        context = {'order': order, 'items': order.items.all(), 'invoice': None, 'user': self.individual}
        text = render_to_string('payments/email/order_confirmation_message.txt', context)
        self.assertIn('149,00 € TTC', text)
        self.assertIn('Total payé : 149,00 € (TVA comprise)', text)
        self.assertNotIn('HTVA', text)

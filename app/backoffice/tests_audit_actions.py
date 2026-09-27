"""
Fichier : tests_audit_actions.py
Projet : Marketplace SMARTOPS
Application : backoffice
Description : Les actions d'administration du back-office sont consignées dans le journal applicatif.
"""

import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from catalog.models import Category, Module
from payments.models import Order

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BackofficeAuditActionsTests(TestCase):

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        self.admin = User.objects.create_superuser('root_bo', 'root_bo@example.org', 'x')
        self.customer = User.objects.create_user('client_bo', 'client_bo@example.org', 'x', is_client=True)
        self.client.force_login(self.admin)

    def output_of(self, action):
        with self.assertLogs('audit', level='INFO') as captured:
            action()
        return '\n'.join(captured.output)

    def test_password_reset_sent_and_failed(self):
        url = reverse('backoffice:user_password_reset', args=[self.customer.pk])
        output = self.output_of(lambda: self.client.post(url))
        self.assertIn(f'BACKOFFICE PASSWORD RESET SENT: Reset email sent to client client_bo (ID: {self.customer.pk}) (by root_bo)', output)
        with patch('allauth.account.forms.ResetPasswordForm.save', side_effect=OSError('SMTP indisponible')):
            output = self.output_of(lambda: self.client.post(url))
        self.assertIn('BACKOFFICE PASSWORD RESET FAILED', output)
        self.assertIn('OSError: SMTP indisponible', output)

    def test_refund_processed(self):
        order = Order.objects.create(user=self.customer, status='refund_pending', total_amount=Decimal('59.96'),
                                     refund_due_amount=Decimal('10.00'))
        output = self.output_of(lambda: self.client.post(
            reverse('backoffice:order_mark_refund_processed', args=[order.pk])))
        self.assertIn(f'BACKOFFICE REFUND PROCESSED: Order #{order.pk} marked as refunded', output)

    def test_catalog_changes(self):
        output = self.output_of(lambda: self.client.post(reverse('backoffice:category_create'),
                                                          {'name_fr': 'Énergie', 'name_en': 'Energy', 'name_nl': 'Energie',
                                                           'slug_fr': 'energie', 'slug_en': 'energy', 'slug_nl': 'energie-nl',
                                                           'icon': 'las la-bolt'}))
        self.assertIn('BACKOFFICE CATEGORY CREATE: Category Énergie', output)
        module = Module.objects.create(name='Module Supprimé', slug='module-supprime',
                                       category=Category.objects.get(slug_fr='energie'), price=Decimal('10'))
        output = self.output_of(lambda: self.client.post(reverse('backoffice:module_delete', args=[module.pk])))
        self.assertIn(f'BACKOFFICE MODULE DELETE: Module Module Supprimé (ID: {module.pk}) (by root_bo)', output)

    def test_logs_cleared_is_traced(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'logs').mkdir()
            (Path(tmp) / 'logs' / 'audit.log').write_text('[2026-09-27 10:00:00,000] INFO audit ANCIEN\n')
            with override_settings(BASE_DIR=Path(tmp)):
                output = self.output_of(lambda: self.client.get(reverse('backoffice:logs_view') + '?action=clear'))
        self.assertIn('BACKOFFICE LOGS CLEARED', output)

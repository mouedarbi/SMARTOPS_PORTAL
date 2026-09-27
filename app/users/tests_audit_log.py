"""
Fichier : tests_audit_log.py
Projet : Marketplace SMARTOPS
Application : users
Description : Journalisation des événements de compte dans le journal applicatif (logger « audit »).
"""

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

User = get_user_model()
PASSWORD = 'Bon-Mot-De-Passe1'


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   SECURE_SSL_REDIRECT=False,
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountAuditLogTests(TestCase):

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        self.user = User.objects.create_user('journal', 'journal@example.org', PASSWORD, is_client=True)

    def logs_of(self, action):
        with self.assertLogs('audit', level='INFO') as captured:
            action()
        return '\n'.join(captured.output)

    def test_login_success_and_failure(self):
        output = self.logs_of(lambda: self.client.post(
            reverse('account_login'), {'login': 'journal@example.org', 'password': 'mauvais'},
            HTTP_X_REAL_IP='203.0.113.5'))
        self.assertIn("AUTH LOGIN FAILED: Identifier 'journal@example.org' from IP 203.0.113.5", output)
        self.assertNotIn('mauvais', output)
        output = self.logs_of(lambda: self.client.post(
            reverse('account_login'), {'login': 'journal@example.org', 'password': PASSWORD}))
        self.assertIn(f'AUTH LOGIN SUCCESS: User journal (ID: {self.user.pk})', output)
        self.assertNotIn(PASSWORD, output)

    def test_logout(self):
        self.client.force_login(self.user)
        output = self.logs_of(lambda: self.client.post(reverse('account_logout')))
        self.assertIn('AUTH LOGOUT: User journal', output)

    def test_signup(self):
        output = self.logs_of(lambda: self.client.post(reverse('account_signup'), {
            'username': 'inscrit', 'email': 'inscrit@example.org',
            'password1': 'SecurPass12345!', 'password2': 'SecurPass12345!'}))
        self.assertIn('ACCOUNT SIGNUP SUCCESS: User inscrit', output)

    def test_password_reset_request_known_and_unknown_email(self):
        output = self.logs_of(lambda: self.client.post(reverse('account_reset_password'),
                                                       {'email': 'journal@example.org'}))
        self.assertIn('PASSWORD RESET REQUESTED: Reset link sent to journal@example.org', output)
        output = self.logs_of(lambda: self.client.post(reverse('account_reset_password'),
                                                       {'email': 'inconnu@example.org'}))
        self.assertIn('PASSWORD RESET REQUEST FAILED: No active account for email inconnu@example.org', output)

    def test_password_change(self):
        self.client.force_login(self.user)
        output = self.logs_of(lambda: self.client.post(reverse('account_change_password'), {
            'oldpassword': PASSWORD, 'password1': 'Nouveau-Mot-De-Passe2', 'password2': 'Nouveau-Mot-De-Passe2'}))
        self.assertIn('PASSWORD CHANGE SUCCESS: User journal', output)
        self.assertNotIn('Nouveau-Mot-De-Passe2', output)

    def test_email_send_failure_is_logged(self):
        with override_settings(EMAIL_BACKEND='users.tests_audit_log.FailingBackend'):
            with self.assertLogs('audit', level='INFO') as captured:
                with self.assertRaises(OSError):
                    self.client.post(reverse('account_reset_password'), {'email': 'journal@example.org'})
        self.assertIn('EMAIL SEND FAILED', '\n'.join(captured.output))

    def test_account_deletion(self):
        self.client.force_login(self.user)
        output = self.logs_of(lambda: self.client.post(reverse('users:delete_account_confirm'),
                                                       {'confirmation': 'SUPPRIMER'}))
        self.assertIn(f'ACCOUNT DELETION SUCCESS: User journal (ID: {self.user.pk})', output)

    def test_admin_update_and_anonymization(self):
        admin = User.objects.create_superuser('root_audit', 'root_audit@example.org', 'x')
        self.client.force_login(admin)
        output = self.logs_of(lambda: self.client.post(
            reverse('admin:users_user_changelist'),
            {'action': 'anonymize_accounts', '_selected_action': [self.user.pk]}))
        self.assertIn(f'ADMIN ACCOUNT ANONYMIZED: User journal (ID: {self.user.pk}) anonymized by root_audit', output)


class FailingBackend:
    def __init__(self, *args, **kwargs):
        pass

    def send_messages(self, messages):
        raise OSError('SMTP indisponible')

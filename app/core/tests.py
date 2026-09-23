"""
Fichier : tests.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Tests de validation pour l'application core.
"""

from django.test import TestCase, Client
from django.urls import reverse

class CoreTest(TestCase):
    """
    Classe de tests pour vérifier que la page d'accueil de core est opérationnelle.
    """

    def test_home_page_status_code(self):
        """
        Vérification que la page d'accueil retourne un code HTTP 200.
        
        @return : None.
        """
        client = Client()
        response = client.get(reverse('core:home'), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_home_page_content(self):
        """
        Vérification que la page d'accueil contient le message de bienvenue.

        @return : None.
        """
        client = Client()
        response = client.get(reverse('core:home'), follow=True)
        self.assertContains(response, "Gestion de Maintenance Assistée par Ordinateur")


class ContactFormTestCase(TestCase):
    """Formulaire de contact de l'accueil (issue #6) : enregistrement en base, sans envoi d'email."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.url = reverse('core:contact_submit')
        self.valid = {'name': 'Jean Dupont', 'email': 'jean@example.org', 'message': 'Bonjour, une question sur un module.'}

    def test_valid_message_is_saved_and_redirects_with_confirmation(self):
        from core.models import ContactMessage
        response = self.client.post(self.url, self.valid)
        self.assertEqual(response.status_code, 302)
        self.assertIn('contact=sent', response['Location'])
        self.assertTrue(response['Location'].endswith('#contact'))
        message = ContactMessage.objects.get()
        self.assertEqual((message.name, message.email, message.is_read), ('Jean Dupont', 'jean@example.org', False))

    def test_invalid_message_is_refused(self):
        from core.models import ContactMessage
        for bad in ({**self.valid, 'email': 'pas-un-email'}, {**self.valid, 'message': 'ok'}, {**self.valid, 'name': ''}):
            response = self.client.post(self.url, bad)
            self.assertIn('contact=error', response['Location'])
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_honeypot_saves_nothing(self):
        from core.models import ContactMessage
        response = self.client.post(self.url, {**self.valid, 'website': 'http://spam.example'})
        self.assertIn('contact=sent', response['Location'])
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_throttle_limits_messages_per_hour(self):
        from core.models import ContactMessage
        from core.views import CONTACT_MAX_PER_HOUR
        for _ in range(CONTACT_MAX_PER_HOUR):
            self.client.post(self.url, self.valid)
        response = self.client.post(self.url, self.valid)
        self.assertIn('contact=error', response['Location'])
        self.assertEqual(ContactMessage.objects.count(), CONTACT_MAX_PER_HOUR)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_home_form_posts_to_contact_endpoint_with_named_fields(self):
        html = self.client.get('/fr/').content.decode()
        self.assertIn(f'action="{self.url}"', html)
        for field in ('name="name"', 'name="email"', 'name="message"', 'name="website"', 'csrfmiddlewaretoken'):
            self.assertIn(field, html)
        confirmation = self.client.get('/fr/?contact=sent').content.decode()
        self.assertIn('bien été enregistré', confirmation)

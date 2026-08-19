"""
Fichier : tests.py
Application : content
Auteur : Mohamed Ouedarbi
Description : Tests unitaires de navigation, multilinguisme et conformité SEO (Sitemap, Robots.txt).
"""

from django.test import TestCase, Client as HttpClient, override_settings
from django.urls import reverse


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PortalNavigationAndSEOTestCase(TestCase):
    def setUp(self):
        self.client_http = HttpClient()

    def test_home_page_rendering_and_seo_tags(self):
        """Vérifie le rendu de la page d'accueil, les métadonnées SEO et le balisage Schema.org."""
        response = self.client_http.get('/fr/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SMARTOPS')
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, 'schema.org')
        self.assertContains(response, 'og:title')

    def test_multilingual_routing(self):
        """Vérifie que les trois langues officielles du portail (FR, EN, NL) sont accessibles."""
        for lang_code in ['fr', 'en', 'nl']:
            response = self.client_http.get(f'/{lang_code}/')
            self.assertEqual(response.status_code, 200, f"Échec d'accès pour la langue {lang_code}")

    def test_robots_txt_and_sitemap_xml(self):
        """Vérifie la bonne distribution des fichiers robots.txt et sitemap.xml."""
        # 1. robots.txt
        resp_robots = self.client_http.get('/robots.txt')
        self.assertEqual(resp_robots.status_code, 200)
        self.assertIn('text/plain', resp_robots.get('Content-Type', ''))

        # 2. sitemap.xml
        resp_sitemap = self.client_http.get('/sitemap.xml')
        self.assertEqual(resp_sitemap.status_code, 200)
        self.assertIn('xml', resp_sitemap.get('Content-Type', ''))

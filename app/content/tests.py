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

    def test_mobile_menu_burger_and_panel(self):
        """Le site public doit fournir un menu burger mobile complet (navigation, langue, compte)."""
        for lang_code in ['fr', 'en', 'nl']:
            html = self.client_http.get(f'/{lang_code}/').content.decode()
            self.assertIn('@click="open = !open"', html)
            self.assertIn('id="mobile-menu"', html)
            self.assertIn('x-cloak', html)
            start = html.index('id="mobile-menu"')
            panel = html[start:html.index('</nav>', start)]
            for target in (reverse('catalog:module_list'), reverse('account_login'), reverse('account_signup')):
                self.assertIn(target, panel)

    def test_mobile_menu_shows_account_links_when_logged_in(self):
        """Connecté : le panneau mobile propose le compte et la déconnexion à la place de la connexion."""
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username='mobile_user', email='m@example.org', password='Password123!')
        self.client_http.force_login(user)
        html = self.client_http.get('/fr/').content.decode()
        start = html.index('id="mobile-menu"')
        panel = html[start:html.index('</nav>', start)]
        self.assertIn(reverse('users:dashboard'), panel)
        self.assertIn(reverse('account_logout'), panel)
        self.assertNotIn(reverse('account_signup'), panel)

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


class FaviconTestCase(TestCase):
    """Le favicon existe et est référencé par le site public."""

    def test_icon_files_are_real_images(self):
        from django.contrib.staticfiles import finders
        import os
        for name in ('images/favicon.ico', 'images/favicon-32x32.png', 'images/apple-touch-icon.png'):
            path = finders.find(name)
            self.assertIsNotNone(path, name)
            self.assertGreater(os.path.getsize(path), 500, name)

    def test_public_pages_reference_the_favicon(self):
        html = self.client.get('/fr/').content.decode()
        self.assertIn('favicon.ico', html)
        self.assertIn('apple-touch-icon', html)
        self.assertIn('name="theme-color"', html)

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


class LegalPagesAccountDeletionTestCase(TestCase):
    """CGV et confidentialité décrivent le remboursement à la suppression du compte et l'anonymisation différée."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')

    def test_privacy_policy_states_the_anonymization_delay(self):
        self.assertContains(self.client.get('/fr/content/confidentialite/'), 'dans un délai de\n        30 jours')
        self.assertContains(self.client.get('/en/content/confidentialite/'), 'permanently anonymized within 30 days')
        self.assertContains(self.client.get('/nl/content/confidentialite/'), 'binnen 30 dagen definitief geanonimiseerd')

    def test_terms_describe_the_refund_on_account_deletion(self):
        self.assertContains(self.client.get('/fr/content/cgv/'), 'Remboursement à la suppression du compte')
        self.assertContains(self.client.get('/en/content/cgv/'), 'Refund on account deletion')
        self.assertContains(self.client.get('/nl/content/cgv/'), 'Terugbetaling bij verwijdering van de account')


class LegalPagesProfessionalAccountsTestCase(TestCase):
    """CGV et confidentialité décrivent les factures et l'absence de remboursement pour les comptes professionnels."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')

    def test_terms_and_privacy_policy_mention_professional_accounts(self):
        self.assertContains(self.client.get('/fr/content/cgv/'), 'Le droit de rétractation est réservé aux consommateurs')
        self.assertContains(self.client.get('/en/content/cgv/'), 'Individual accounts do not receive an invoice')
        self.assertContains(self.client.get('/nl/content/confidentialite/'), 'Factuurgegevens van professionele accounts')


class PrivacyPolicyCookiesTestCase(TestCase):
    """Cookies réellement posés par le Portal : messages listé ; aucun cookie Stripe (paiement sur la page de Stripe)."""

    def setUp(self):
        from django.utils import translation
        self.addCleanup(translation.activate, 'fr')

    def test_cookie_table_matches_what_the_portal_sets(self):
        response = self.client.get('/fr/content/confidentialite/')
        self.assertContains(response, '>messages</td>')
        self.assertNotContains(response, '__stripe_mid')
        self.assertContains(response, 'applique sa propre politique de cookies')

    def test_stripe_paragraph_is_translated(self):
        self.assertContains(self.client.get('/en/content/confidentialite/'), 'Stripe applies its own cookie policy')
        self.assertContains(self.client.get('/nl/content/confidentialite/'), 'Stripe past daar zijn eigen cookiebeleid toe')


class NoThirdPartyAssetsTestCase(TestCase):
    """Aucune ressource (script, feuille de style, police) n'est chargée depuis un serveur tiers : l'adresse IP
    des visiteurs n'est transmise à aucun CDN (RGPD). Les fichiers sont servis depuis core/static/vendor."""

    def test_templates_reference_no_external_script_or_stylesheet(self):
        import re
        from pathlib import Path
        from django.conf import settings
        pattern = re.compile(r'<(?:script|link)\\b[^>]*(?:src|href)="(?:https?:)?//', re.I)
        offenders = [str(path.relative_to(settings.BASE_DIR))
                     for path in Path(settings.BASE_DIR).rglob('*.html')
                     if 'venv' not in path.parts and 'static' not in path.parts and pattern.search(path.read_text(encoding='utf-8'))]
        self.assertEqual(offenders, [])

    def test_public_and_backoffice_pages_load_local_assets(self):
        from django.contrib.auth import get_user_model
        html = self.client.get('/fr/').content.decode()
        self.assertIn('vendor/tailwindcss/tailwindcss-3.4.17', html)
        self.assertIn('vendor/alpinejs/alpinejs-3.17.4.min', html)
        get_user_model().objects.create_superuser('root', 'root@example.org', 'x')
        self.client.login(username='root@example.org', password='x')
        html = self.client.get('/fr/backoffice/modules/create/').content.decode()
        self.assertIn('vendor/line-awesome/css/line-awesome.min', html)
        self.assertIn('vendor/bootstrap/css/bootstrap.min', html)

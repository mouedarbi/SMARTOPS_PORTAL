"""
Fichier : tests.py
Projet : Marketplace SMARTOPS
Application : content
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Tests unitaires pour l'application de contenu (Wagtail CMS).
              Vérifie la création et l'intégrité des modèles de pages.
"""

from django.test import TestCase
from wagtail.models import Page
from content.models import ContentIndexPage, ContentPage
import datetime

class ContentModelsTests(TestCase):
    """
    Suite de tests pour les modèles de contenu Wagtail.
    """

    def setUp(self):
        """
        Configuration de l'environnement de test : récupération de la page racine.
        """
        self.root_page = Page.objects.get(id=1)

    def test_create_content_index_page(self):
        """
        Vérifie la création d'une page d'index de contenu.
        """
        index_page = ContentIndexPage(
            title="Blog SMARTOPS",
            slug="blog",
            intro="Bienvenue sur notre blog."
        )
        self.root_page.add_child(instance=index_page)
        self.assertEqual(index_page.title, "Blog SMARTOPS")
        self.assertTrue(index_page.live)

    def test_create_content_page(self):
        """
        Vérifie la création d'une page de contenu liée à un index.
        """
        # Création de l'index d'abord
        index_page = ContentIndexPage(title="Doc", slug="doc", intro="Doc intro")
        self.root_page.add_child(instance=index_page)
        
        # Création de la page de contenu
        content_page = ContentPage(
            title="Installation de SMARTOPS",
            slug="installation",
            date=datetime.date.today(),
            body="Voici comment installer le produit."
        )
        index_page.add_child(instance=content_page)
        
        self.assertEqual(content_page.title, "Installation de SMARTOPS")
        self.assertEqual(content_page.get_parent(), index_page)

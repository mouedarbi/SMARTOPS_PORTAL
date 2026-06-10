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
        self.assertContains(response, "La GMAO open source")

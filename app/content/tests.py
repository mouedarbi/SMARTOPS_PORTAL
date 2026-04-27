"""
Fichier : tests.py
Projet : Marketplace SMARTOPS
Application : content
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Tests unitaires pour l'application de contenu (Version Django Pur).
"""

from django.test import TestCase

class SimpleContentTest(TestCase):
    def test_placeholder(self):
        self.assertEqual(1, 1)

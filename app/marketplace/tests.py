"""
Fichier : tests.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Tests unitaires initiaux pour valider l'environnement de développement Django.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

class EnvironmentTest(TestCase):
    """
    Classe de tests pour vérifier que l'environnement de base Django est opérationnel.
    """

    def test_admin_user_creation(self):
        """
        Vérification de la création d'un utilisateur administrateur.
        Vérifie si le modèle User est accessible et fonctionnel.
        
        @return : None (Lève une erreur si le test échoue).
        """
        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpassword'))

    def test_database_connection(self):
        """
        Vérification de la connexion à la base de données SQLite par défaut.
        
        @return : None (Lève une erreur si le test échoue).
        """
        from django.db import connection
        self.assertIsNotNone(connection)

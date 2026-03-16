"""
Tests de base pour la validation de l'environnement Django Marketplace.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

class EnvironmentTest(TestCase):
    """
    Vérifie que l'environnement de base Django est opérationnel.
    """

    def test_admin_user_creation(self):
        """
        Vérifie que nous pouvons créer un utilisateur et que le modèle User est accessible.
        """
        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpassword'))

    def test_database_connection(self):
        """
        Vérifie que la connexion à la base de données SQLite fonctionne.
        """
        from django.db import connection
        self.assertIsNotNone(connection)

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import Module, Category, Review
from licensing.models import License

User = get_user_model()

class ModuleReviewTestCase(TestCase):
    """
    Tests unitaires pour valider le système d'avis et d'évaluations :
    1. Un utilisateur anonyme ne peut pas poster (redirection).
    2. Un utilisateur connecté sans licence/achat ne peut pas poster.
    3. Un utilisateur connecté avec licence peut poster, et le commentaire est traduit par LibreTranslate.
    """

    def setUp(self):
        # 1. Création des utilisateurs
        self.user_without_license = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='password123',
            is_client=True
        )
        self.user_with_license = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='password123',
            is_client=True
        )

        # 2. Création de la catégorie et du module
        self.category = Category.objects.create(
            name='IoT',
            slug='iot'
        )
        self.module = Module.objects.create(
            name='Module IoT Surveillance',
            slug='module-iot-surveillance',
            price=99.00,
            category=self.category,
            is_active=True
        )

        # 3. Attribution d'une licence pour user2
        self.license = License.objects.create(
            user=self.user_with_license,
            module=self.module,
            is_active=True,
            max_activations=1
        )

        self.client = Client()

    def test_anonymous_user_cannot_post_review(self):
        """
        Vérifie qu'un visiteur anonyme est redirigé lors d'une tentative de POST, et aucun avis n'est créé.
        """
        # Utilisation de l'URL préfixée manuellement en français (/fr/) pour court-circuiter les redirections 301 de langue
        detail_url = f'/fr/catalog/{self.module.slug}/'
        response = self.client.post(detail_url, {
            'rating': 5,
            'comment': 'Super module !'
        }, follow=True)
        
        # L'avis ne doit pas être créé
        self.assertEqual(Review.objects.filter(module=self.module).count(), 0)
        
        # Message d'erreur attendu
        messages = list(response.context['messages'])
        self.assertTrue(any("connecté" in str(m) for m in messages))

    def test_user_without_license_cannot_post_review(self):
        """
        Vérifie qu'un utilisateur connecté mais ne disposant pas d'une licence active
        reçoit un message d'erreur et ne peut pas créer de Review.
        """
        self.client.login(username='user1', password='password123')
        detail_url = f'/fr/catalog/{self.module.slug}/'
        
        response = self.client.post(detail_url, {
            'rating': 4,
            'comment': 'Je veux commenter mais je n\'ai pas acheté.'
        }, follow=True)
        
        # L'avis ne doit pas être créé
        self.assertEqual(Review.objects.filter(module=self.module).count(), 0)
        
        # Message d'erreur attendu
        messages = list(response.context['messages'])
        self.assertTrue(any("licence active" in str(m) for m in messages))

    def test_user_with_license_can_post_review_and_auto_translate(self):
        """
        Vérifie qu'un utilisateur possédant une licence peut soumettre un avis,
        et que celui-ci est automatiquement traduit via LibreTranslate (FR -> EN, NL).
        """
        # Tentative de connexion
        login_success = self.client.login(username='user2', password='password123')
        self.assertTrue(login_success)
        
        detail_url = f'/fr/catalog/{self.module.slug}/'
        response = self.client.post(detail_url, {
            'rating': 5,
            'comment': 'Excellent travail sur ce plugin, très stable.'
        }, follow=True)
        
        # L'avis doit être créé
        self.assertEqual(Review.objects.filter(module=self.module).count(), 1)
        
        review = Review.objects.get(module=self.module, user=self.user_with_license)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent travail sur ce plugin, très stable.')
        self.assertEqual(review.comment_language, 'fr')
        
        # Vérification des traductions automatiques par LibreTranslate
        self.assertEqual(review.comment_fr, 'Excellent travail sur ce plugin, très stable.')
        self.assertIsNotNone(review.comment_en)
        self.assertIsNotNone(review.comment_nl)
        
        # Si le serveur LibreTranslate tourne, les traductions ne doivent pas être vides
        self.assertNotEqual(review.comment_en, '')
        self.assertNotEqual(review.comment_nl, '')
        
        # Message de succès attendu
        messages = list(response.context['messages'])
        self.assertTrue(any("traduit automatiquement" in str(m) for m in messages))

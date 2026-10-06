"""
Fichier : populate_portal_clients.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Script de démonstration : crée 100 comptes clients fictifs, dont 70 % de
              professionnels (exécutable uniquement avec DEBUG=True).
"""

import os
import sys
import django
import random

# Configuration Django et ajout du chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

from users.demo_data import demo_email, fictitious_company, is_professional_slot
from users.models import BillingProfile

User = get_user_model()

def run():
    """Crée les 100 comptes clients de démonstration (refusé si DEBUG est désactivé)."""
    # Script de démonstration : il supprime des données. Refusé hors environnement de développement.
    if not settings.DEBUG:
        sys.exit("Refusé : script de données de test, exécutable uniquement avec DEBUG=True (jamais en production).")
    print("Début de la génération de 100 utilisateurs clients sur le portail...")
    
    # Vérifier l'admin du portail
    admin_user = User.objects.filter(username='admin').first()
    if admin_user:
        print("Admin existant trouvé : admin")
    else:
        # Mot de passe fourni par l'environnement, jamais écrit dans le code source.
        admin_password = os.environ.get('PORTAL_ADMIN_PASSWORD')
        if not admin_password:
            sys.exit("Définissez PORTAL_ADMIN_PASSWORD pour créer le compte admin de démonstration.")
        print("Création de l'admin par défaut...")
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', admin_password)
        print("Admin créé : username=admin")

    # Noms et prénoms réalistes belges
    first_names = ["Jean", "Michel", "Pierre", "Philippe", "Marc", "David", "Thomas", "Nicolas", "Laurent", "Olivier",
                   "Marie", "Nathalie", "Isabelle", "Sylvie", "Catherine", "Françoise", "Anne", "Monique", "Valérie", "Sandrine"]
    last_names = ["Peeters", "Janssens", "Maes", "Jacobs", "Mertens", "Claes", "Wauters", "Goossens", "Lambrechts", "De Smet",
                  "Vandenberghe", "Dubois", "Lambert", "Martin", "Dupont", "Simon", "Laurent", "Michel", "Garcia", "Thomas"]

    # Nettoyage des anciens utilisateurs de test (non superusers et non staff)
    print("Nettoyage des anciens comptes de test...")
    User.objects.filter(is_superuser=False, is_staff=False).delete()

    created_clients = 0

    for i in range(100):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        username = f"{fn.lower()}.{ln.lower()}{random.randint(10, 99)}"
        # Plus addressing Gmail : les e-mails des comptes fictifs arrivent dans la boîte du projet.
        email = demo_email(i + 1)
        professional = is_professional_slot(i)

        user = User.objects.create(
            username=username,
            email=email,
            first_name=fn,
            last_name=ln,
            is_client=True,
            language_preference='fr',
            account_type='professional' if professional else 'individual',
        )
        user.set_password('clientpassword123')
        user.save()
        if professional:
            BillingProfile.objects.create(user=user, **fictitious_company(random.Random(i), fn, ln))
        created_clients += 1

    print(f"Population terminée ! {created_clients} comptes de clients créés avec succès, 70 % professionnels "
          f"(mot de passe : clientpassword123).")

if __name__ == '__main__':
    run()

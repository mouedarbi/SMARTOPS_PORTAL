import os
import sys
import django
import random

# Configuration Django et ajout du chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def run():
    print("Début de la génération de 100 utilisateurs clients sur le portail...")
    
    # Vérifier l'admin du portail
    admin_user = User.objects.filter(username='admin').first()
    if admin_user:
        print("Admin existant trouvé : admin")
    else:
        print("Création de l'admin par défaut...")
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword123')
        print("Admin créé : username=admin, password=adminpassword123")

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
        email = f"{username}@example.be"
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=fn,
            last_name=ln,
            is_client=True,
            language_preference='fr'
        )
        user.set_password('clientpassword123')
        user.save()
        created_clients += 1

    print(f"Population terminée ! {created_clients} comptes de clients créés avec succès (mot de passe : clientpassword123).")

if __name__ == '__main__':
    run()

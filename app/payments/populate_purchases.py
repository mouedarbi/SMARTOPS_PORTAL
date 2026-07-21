import os
import sys
import django
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone

# Configuration Django et ajout du chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from django.contrib.auth import get_user_model
from catalog.models import Module, ModuleBundle
from payments.models import Order, OrderItem
from licensing.models import License

User = get_user_model()

def generate_stripe_id():
    """Génère un faux ID de transaction Stripe PaymentIntent réaliste."""
    chars = string.ascii_letters + string.digits
    rand_str = ''.join(random.choice(chars) for _ in range(24))
    return f"pi_{rand_str}"

def get_random_date_last_90_days():
    """Génère une date aléatoire au cours des 90 derniers jours."""
    now = timezone.now()
    days_ago = random.randint(0, 90)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    random_date = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    return random_date

def run():
    print("Début de la génération d'historiques d'achats réalistes...")
    
    # 1. Récupération des clients (is_client=True)
    clients = User.objects.filter(is_client=True)
    if not clients.exists():
        print("Erreur : Aucun client trouvé en base de données. Veuillez d'abord exécuter populate_portal_clients.py.")
        return

    # 2. Récupération des modules et packs actifs
    modules = list(Module.objects.filter(is_active=True))
    bundles = list(ModuleBundle.objects.filter(is_active=True))
    
    if not modules and not bundles:
        print("Erreur : Aucun module ou pack actif trouvé en base de données.")
        return

    print(f"Trouvé : {len(clients)} clients, {len(modules)} modules, {len(bundles)} packs.")
    
    # Statistiques globales
    total_orders = 0
    total_items = 0
    total_licenses = 0
    total_revenue = 0.0

    # Nettoyage optionnel : on supprime les commandes et licences de simulation précédentes pour éviter les doublons
    # (Mais on garde les comptes utilisateurs existants !)
    print("Nettoyage des commandes, éléments de commande et licences existants...")
    License.objects.all().delete()
    OrderItem.objects.all().delete()
    Order.objects.all().delete()

    for idx, client in enumerate(clients, 1):
        # Chaque client achète de 1 à 3 fois
        num_purchases = random.choice([1, 1, 1, 2, 2, 3]) # Distribution orientée vers 1 ou 2 achats
        
        # Liste des modules que ce client a déjà acquis (pour éviter les doublons de licence)
        acquired_module_ids = set()

        for _ in range(num_purchases):
            # 70% de chance d'acheter un module individuel, 30% d'acheter un pack
            is_bundle = random.random() < 0.30
            
            selected_item = None
            price = 0.0
            
            if is_bundle and bundles:
                # Filtrer les bundles pour ne pas acheter un pack dont l'utilisateur possède déjà tous les modules
                valid_bundles = []
                for b in bundles:
                    b_mod_ids = set(m.id for m in b.modules.all())
                    if not b_mod_ids.issubset(acquired_module_ids):
                        valid_bundles.append(b)
                
                if valid_bundles:
                    selected_item = random.choice(valid_bundles)
                    price = float(selected_item.final_price)
                else:
                    is_bundle = False # Repli sur module individuel
            
            if not is_bundle and modules:
                # Filtrer les modules restants non encore acquis
                valid_modules = [m for m in modules if m.id not in acquired_module_ids]
                if valid_modules:
                    selected_item = random.choice(valid_modules)
                    price = float(selected_item.price)
            
            if not selected_item:
                continue # Plus rien d'éligible à acheter pour cet utilisateur

            # Création de la commande
            stripe_id = generate_stripe_id()
            purchase_date = get_random_date_last_90_days()
            
            order = Order.objects.create(
                user=client,
                status='completed',
                total_amount=price,
                stripe_payment_intent_id=stripe_id
            )
            # Force la date historique (car auto_now_add=True empêche la modification directe à la création)
            Order.objects.filter(id=order.id).update(created_at=purchase_date)
            
            # Création de l'OrderItem et de la licence correspondante
            if isinstance(selected_item, ModuleBundle):
                OrderItem.objects.create(
                    order=order,
                    bundle=selected_item,
                    price_at_purchase=price
                )
                # Licences pour tous les modules du pack
                for mod in selected_item.modules.all():
                    License.objects.get_or_create(
                        user=client,
                        module=mod,
                        defaults={'is_active': True, 'max_activations': 1}
                    )
                    acquired_module_ids.add(mod.id)
                    total_licenses += 1
            else:
                OrderItem.objects.create(
                    order=order,
                    module=selected_item,
                    price_at_purchase=price
                )
                License.objects.get_or_create(
                    user=client,
                    module=selected_item,
                    defaults={'is_active': True, 'max_activations': 1}
                )
                acquired_module_ids.add(selected_item.id)
                total_licenses += 1
                
            total_orders += 1
            total_items += 1
            total_revenue += price
            
        if idx % 20 == 0:
            print(f"Progression : {idx}/100 clients traités...")

    print("\n--- SYNTHÈSE DE LA GÉNÉRATION D'ACHATS ---")
    print(f"Total Commandes générées : {total_orders}")
    print(f"Total Éléments achetés   : {total_items}")
    print(f"Total Licences actives   : {total_licenses}")
    print(f"Chiffre d'Affaires total : {total_revenue:,.2f} €")
    print("------------------------------------------")
    print("Opération terminée avec succès !")

if __name__ == "__main__":
    run()

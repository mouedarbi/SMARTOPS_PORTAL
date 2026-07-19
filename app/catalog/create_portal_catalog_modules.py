import os
import sys
import django
from decimal import Decimal

# Configuration Django et ajout du chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from catalog.models import Category, Module

def run():
    print("Début de la création des fiches de modules sur le catalogue du portail...")

    # 1. Création des catégories avec traductions
    categories_data = [
        {
            "name_fr": "Planification & Logistique",
            "name_en": "Planning & Logistics",
            "icon": "📅"
        },
        {
            "name_fr": "Gestion d'Équipe & RH",
            "name_en": "Team Management & HR",
            "icon": "👥"
        },
        {
            "name_fr": "Client & Administratif",
            "name_en": "Client & Administrative",
            "icon": "📄"
        },
        {
            "name_fr": "Objets Connectés & IoT",
            "name_en": "Connected Devices & IoT",
            "icon": "🔌"
        },
        {
            "name_fr": "Gestion des Stocks",
            "name_en": "Stock Management",
            "icon": "📦"
        }
    ]

    categories_objs = {}
    for cat in categories_data:
        from django.utils.text import slugify
        slug_fr = slugify(cat["name_fr"])
        slug_en = slugify(cat["name_en"])
        
        category, created = Category.objects.update_or_create(
            slug_fr=slug_fr,
            defaults={
                "name_fr": cat["name_fr"],
                "name_en": cat["name_en"],
                "slug_en": slug_en,
                "icon": cat["icon"]
            }
        )
        categories_objs[cat["name_fr"]] = category
        print(f"Catégorie '{cat['name_fr']}' prête.")

    # 2. Mettre à jour l'ancien module "Localisation des sites" s'il existe pour le mettre dans la bonne catégorie
    map_module = Module.objects.filter(slug_fr='localisation-des-sites').first()
    if map_module:
        map_module.category = categories_objs["Planification & Logistique"]
        map_module.save()
        print("Ancien module 'Localisation des sites' rattaché à la catégorie 'Planification & Logistique'.")

    # 3. Données des nouveaux modules (uniquement les fiches produits)
    modules_data = [
        {
            "name_fr": "Contrats de Maintenance",
            "name_en": "Maintenance Contracts",
            "category": "Planification & Logistique",
            "short_desc_fr": "Planifiez et automatisez vos interventions récurrentes.",
            "short_desc_en": "Schedule and automate your recurring interventions.",
            "desc_fr": "Automatisez la planification de vos interventions récurrentes. Créez des contrats de maintenance mensuels, trimestriels, semestriels ou annuels pour vos clients et laissez le système générer automatiquement les tickets d'intervention à l'avance.",
            "desc_en": "Automate the planning of your recurring maintenance tasks. Create monthly, quarterly, semi-annual, or annual maintenance contracts for your clients and let the system automatically generate upcoming intervention tickets.",
            "price": Decimal("149.00")
        },
        {
            "name_fr": "Gestion de la Flotte Véhicules",
            "name_en": "Fleet Management",
            "category": "Planification & Logistique",
            "short_desc_fr": "Suivez et attribuez les véhicules de société aux techniciens.",
            "short_desc_en": "Track and assign company vehicles to technicians.",
            "desc_fr": "Gérez efficacement la flotte de véhicules de l'entreprise. Suivez l'attribution des véhicules de service aux techniciens, enregistrez les dates de contrôles techniques et assurez-vous que vos techniciens disposent du bon matériel pour leurs interventions de maintenance.",
            "desc_en": "Manage your company fleet effectively. Track assignment of service vehicles to technicians, store inspection dates, and ensure your technicians have the right vehicles for their tasks.",
            "price": Decimal("89.00")
        },
        {
            "name_fr": "HRM - Absences & Redistribution de Charge",
            "name_en": "HRM - Absences & Workload Redistribution",
            "category": "Gestion d'Équipe & RH",
            "short_desc_fr": "Gérez les congés et réassignez automatiquement les tickets.",
            "short_desc_en": "Manage leaves and automatically reassign tickets.",
            "desc_fr": "Suivez les congés, absences et heures prestées de vos techniciens. Ce module analyse en temps réel la charge journalière de travail et redistribue automatiquement les tickets d'un technicien malade ou absent vers ses collègues disponibles.",
            "desc_en": "Track leaves, absences, and hours worked. This module analyzes daily workload in real time and automatically reassigns tickets from an absent technician to available colleagues.",
            "price": Decimal("199.00")
        },
        {
            "name_fr": "Signature Électronique & Rapports PDF",
            "name_en": "E-Signature & PDF Reports",
            "category": "Client & Administratif",
            "short_desc_fr": "Faites signer vos bons d'intervention et générez des rapports PDF.",
            "short_desc_en": "Get intervention reports signed and generate PDFs.",
            "desc_fr": "Améliorez la satisfaction client et simplifiez votre facturation. Permettez à vos techniciens de faire signer électroniquement les rapports d'intervention directement sur tablette ou smartphone, avec génération automatique de PV de réception en PDF envoyé par email.",
            "desc_en": "Enhance client satisfaction and simplify billing. Enable technicians to capture electronic signatures directly on tablet or mobile, generating PDF reports sent automatically by email.",
            "price": Decimal("79.00")
        },
        {
            "name_fr": "IoT & Alertes Prédictives",
            "name_en": "IoT & Predictive Alerts",
            "category": "Objets Connectés & IoT",
            "short_desc_fr": "Connectez vos équipements à des capteurs et prévenez les pannes.",
            "short_desc_en": "Connect your equipments to sensors and prevent failures.",
            "desc_fr": "Connectez vos équipements à des capteurs de température, pression ou vibration. Le système surveille en continu l'état de fonctionnement de vos machines et génère automatiquement un ticket d'urgence dès qu'un seuil critique est dépassé.",
            "desc_en": "Connect your assets to temperature, pressure, or vibration sensors. The system continuously monitors machine health and generates urgent tickets as soon as a threshold is crossed.",
            "price": Decimal("299.00")
        },
        {
            "name_fr": "Stock & Pièces Détachées",
            "name_en": "Stock & Spare Parts",
            "category": "Gestion des Stocks",
            "short_desc_fr": "Gérez l'inventaire de vos consommables et pièces de rechange.",
            "short_desc_en": "Manage inventory of spare parts and consumables.",
            "desc_fr": "Suivez en temps réel l'inventaire de vos pièces détachées en entrepôt. Liez les pièces consommées (filtres, joints, courroies) directement aux fiches d'intervention et configurez des alertes de réapprovisionnement automatique pour ne jamais être en rupture.",
            "desc_en": "Track your warehouse spare parts inventory in real-time. Link consumed parts directly to intervention reports and configure low-stock alerts to prevent supply shortages.",
            "price": Decimal("119.00")
        }
    ]

    for mod in modules_data:
        from django.utils.text import slugify
        slug_fr = slugify(mod["name_fr"])
        slug_en = slugify(mod["name_en"])
        
        module, created = Module.objects.update_or_create(
            slug_fr=slug_fr,
            defaults={
                "name_fr": mod["name_fr"],
                "name_en": mod["name_en"],
                "slug_en": slug_en,
                "category": categories_objs[mod["category"]],
                "short_description_fr": mod["short_desc_fr"],
                "short_description_en": mod["short_desc_en"],
                "description_fr": mod["desc_fr"],
                "description_en": mod["desc_en"],
                "price": mod["price"],
                "is_active": True
            }
        )
        print(f"Module '{mod['name_fr']}' enregistré dans le catalogue.")

    print("Catalogue complété avec succès !")

if __name__ == '__main__':
    run()

import os
import sys
import django
from decimal import Decimal

# Configuration Django et ajout du chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from catalog.models import Module, ModuleBundle

def run():
    print("Début de la création des packs de modules sur le catalogue...")

    # Nettoyage des anciens packs
    print("Nettoyage des anciens packs...")
    ModuleBundle.objects.all().delete()

    # Récupérer l'ensemble des modules pour les associations
    contracts_mod = Module.objects.filter(slug_fr="contrats-de-maintenance").first()
    vehicles_mod = Module.objects.filter(slug_fr="gestion-de-la-flotte-vehicules").first()
    hrm_mod = Module.objects.filter(slug_fr="hrm-absences-redistribution-de-charge").first()
    signature_mod = Module.objects.filter(slug_fr="signature-electronique-rapports-pdf").first()
    iot_mod = Module.objects.filter(slug_fr="iot-alertes-predictives").first()
    stock_mod = Module.objects.filter(slug_fr="stock-pieces-detachees").first()

    # 1. Pack Duo "Logistique & Efficacité"
    duo1 = ModuleBundle.objects.create(
        name_fr="Pack Duo Logistique & Efficacité",
        name_en="Logistics & Efficiency Duo Pack",
        slug_fr="pack-duo-logistique-efficacite",
        slug_en="logistics-efficiency-duo-pack",
        short_description_fr="Combinez la planification automatique des contrats et la gestion de flotte.",
        short_description_en="Combine automated contract planning and fleet management.",
        description_fr="Combinez la puissance de la planification automatisée de vos contrats et le suivi de vos véhicules pour maximiser l'efficacité de vos techniciens sur le terrain. Idéal pour les structures en pleine croissance.",
        description_en="Combine the power of automated contract scheduling and vehicle tracking to maximize your field technicians' efficiency. Ideal for growing businesses.",
        discount_mode="PERCENTAGE",
        discount_value=Decimal("15.00"),  # -15%
        is_active=True
    )
    if contracts_mod and vehicles_mod:
        duo1.modules.add(contracts_mod, vehicles_mod)
        print("Pack Duo 1 créé : Logistique & Efficacité.")

    # 2. Pack Duo "RH & Terrain"
    duo2 = ModuleBundle.objects.create(
        name_fr="Pack Duo RH & Terrain",
        name_en="HR & Field Operations Duo Pack",
        slug_fr="pack-duo-rh-terrain",
        slug_en="hr-field-operations-duo-pack",
        short_description_fr="Gérez le planning d'équipe et la signature numérique des rapports.",
        short_description_en="Manage team schedules and digital signature of reports.",
        description_fr="Assurez la continuité de votre service RH avec la gestion intelligente des indisponibilités, tout en digitalisant la signature des bons d'intervention de vos techniciens en direct depuis leur smartphone.",
        description_en="Ensure HR service continuity with smart absence management, while digitalizing the signature of intervention reports directly from your technicians' smartphones.",
        discount_mode="PERCENTAGE",
        discount_value=Decimal("15.00"),  # -15%
        is_active=True
    )
    if hrm_mod and signature_mod:
        duo2.modules.add(hrm_mod, signature_mod)
        print("Pack Duo 2 créé : RH & Terrain.")

    # 3. Pack Duo "Connecté & Préventif"
    duo3 = ModuleBundle.objects.create(
        name_fr="Pack Duo Connecté & Préventif",
        name_en="Connected & Preventive Duo Pack",
        slug_fr="pack-duo-connecte-preventif",
        slug_en="connected-preventive-duo-pack",
        short_description_fr="Connectez vos capteurs IoT au suivi des pièces en stock.",
        short_description_en="Connect your IoT sensors to stock parts tracking.",
        description_fr="Connectez vos équipements à des capteurs de télémesure (IoT) et liez-les au stock des pièces de rechange. Générez des alertes de maintenance prédictives et assurez-vous d'avoir toujours les pièces nécessaires.",
        description_en="Connect your equipments to telemetry sensors (IoT) and link them to spare parts stock. Generate predictive maintenance alerts and ensure you always have the necessary parts in stock.",
        discount_mode="PERCENTAGE",
        discount_value=Decimal("20.00"),  # -20%
        is_active=True
    )
    if iot_mod and stock_mod:
        duo3.modules.add(iot_mod, stock_mod)
        print("Pack Duo 3 créé : Connecté & Préventif.")

    # 4. Pack Intégral "Full SMARTOPS Suite"
    full_bundle = ModuleBundle.objects.create(
        name_fr="Pack Intégral Full SMARTOPS Suite",
        name_en="Integral Full SMARTOPS Suite",
        slug_fr="pack-integral-full-smartops-suite",
        slug_en="integral-full-smartops-suite",
        short_description_fr="L'intégralité des modules premium SMARTOPS à tarif préférentiel.",
        short_description_en="All premium SMARTOPS modules at a discounted price.",
        description_fr="Bénéficiez de la suite complète de gestion de maintenance assistée par ordinateur. L'intégralité des modules premium (Planification, Logistique, RH, Signature, IoT et Stocks) à un tarif exceptionnel de -30%.",
        description_en="Get the complete computer-aided maintenance management suite. All premium modules (Planning, Logistics, HR, E-Signature, IoT, and Stocks) at an exceptional discount of -30%.",
        discount_mode="PERCENTAGE",
        discount_value=Decimal("30.00"),  # -30%
        is_active=True
    )
    all_modules = list(Module.objects.all())
    if all_modules:
        full_bundle.modules.add(*all_modules)
        print(f"Pack Intégral créé avec succès (-30% sur les {len(all_modules)} modules).")

    print("Création des packs complétée avec succès !")

if __name__ == '__main__':
    run()

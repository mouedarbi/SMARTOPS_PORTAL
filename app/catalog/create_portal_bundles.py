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

    # 1. Pack Duo "Logistique & Efficacité"
    duo_bundle = ModuleBundle.objects.create(
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
    
    # Récupérer les modules pour le Pack Duo
    contracts_mod = Module.objects.filter(slug_fr="contrats-de-maintenance").first()
    vehicles_mod = Module.objects.filter(slug_fr="gestion-de-la-flotte-vehicules").first()
    
    if contracts_mod and vehicles_mod:
        duo_bundle.modules.add(contracts_mod, vehicles_mod)
        print("Pack Duo créé avec succès (-15% sur Contrats + Flotte Véhicules).")
    else:
        print("Erreur : Impossible de trouver les modules pour le Pack Duo.")

    # 2. Pack Intégral "Full SMARTOPS Suite"
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
    
    # Ajouter tous les modules existants au pack complet
    all_modules = list(Module.objects.all())
    if all_modules:
        full_bundle.modules.add(*all_modules)
        print(f"Pack Intégral créé avec succès (-30% sur les {len(all_modules)} modules).")
    else:
        print("Erreur : Aucun module trouvé pour le Pack Intégral.")

    print("Création des packs complétée avec succès !")

if __name__ == '__main__':
    run()

import os
import sys
import django
import shutil
import glob

# Configuration Django et ajout du chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from catalog.models import Module

def run():
    print("Début de l'association des images de modules...")

    # Répertoires source et destination
    src_dir = "/root/.gemini/antigravity-cli/brain/427cbca4-d8e1-4fff-9472-31d9ceb6f31b"
    dest_dir = "/root/smartops_portal/SMARTOPS_PORTAL/app/media/modules/featured"
    
    # Créer le répertoire de destination s'il n'existe pas
    os.makedirs(dest_dir, exist_ok=True)

    # Dictionnaire de correspondance slug -> préfixe de fichier image généré
    mappings = {
        "localisation-des-sites": ("map_illustration", "map.jpg"),
        "contrats-de-maintenance": ("contracts_illustration", "contracts.jpg"),
        "gestion-de-la-flotte-vehicules": ("vehicles_illustration", "vehicles.jpg"),
        "hrm-absences-redistribution-de-charge": ("hrm_illustration", "hrm.jpg"),
        "signature-electronique-rapports-pdf": ("signature_illustration", "signature.jpg"),
        "iot-alertes-predictives": ("iot_illustration", "iot.jpg"),
        "stock-pieces-detachees": ("stock_illustration", "stock.jpg"),
    }

    for slug, (img_prefix, dest_name) in mappings.items():
        # Recherche du fichier image le plus récent correspondant au préfixe
        search_pattern = os.path.join(src_dir, f"{img_prefix}_*.jpg")
        found_files = glob.glob(search_pattern)
        
        if not found_files:
            print(f"Alerte : Aucun fichier trouvé pour le préfixe {img_prefix}")
            continue
            
        # Trier pour prendre le plus récent
        found_files.sort(key=os.path.getmtime, reverse=True)
        latest_file = found_files[0]
        
        # Chemin complet de destination
        dest_path = os.path.join(dest_dir, dest_name)
        
        # Copie physique de l'image
        shutil.copy2(latest_file, dest_path)
        print(f"Image copiée : {os.path.basename(latest_file)} -> {dest_name}")
        
        # Mise à jour en base de données
        db_path = f"modules/featured/{dest_name}"
        rows_updated = Module.objects.filter(slug_fr=slug).update(featured_image=db_path)
        if rows_updated:
            print(f"Base de données mise à jour pour le module '{slug}' -> {db_path}")
        else:
            print(f"Erreur : Le module avec le slug '{slug}' n'a pas été trouvé en base de données.")

    print("Association des images complétée avec succès !")

if __name__ == '__main__':
    run()

"""
Nom du fichier : backup_portal.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Commande personnalisée pour sauvegarder l'intégralité des données du portail (Wagtail + Django).
"""

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

class Command(BaseCommand):
    help = "Sauvegarde toutes les données du portail dans une fixture JSON."

    def handle(self, *args, **options):
        # Création du dossier backups s'il n'existe pas
        backup_dir = os.path.join(os.getcwd(), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_smartops_{timestamp}.json"
        filepath = os.path.join(backup_dir, filename)

        self.stdout.write(f"Démarrage de la sauvegarde dans {filename}...")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # On exporte tout sauf les tables de logs techniques et les permissions brutes
                call_command('dumpdata', 
                             exclude=['contenttypes', 'auth.permission', 'wagtailcore.pagelogentry', 'wagtailadmin.editingsession'], 
                             indent=2, 
                             stdout=f)
            
            # Création d'un lien 'latest.json' pour la restauration facile
            latest_path = os.path.join(backup_dir, 'latest.json')
            if os.path.exists(latest_path):
                os.remove(latest_path)
            
            with open(latest_path, 'w', encoding='utf-8') as f:
                call_command('dumpdata', 
                             exclude=['contenttypes', 'auth.permission', 'wagtailcore.pagelogentry', 'wagtailadmin.editingsession'], 
                             indent=2, 
                             stdout=f)

            self.stdout.write(self.style.SUCCESS(f"Sauvegarde réussie : {filepath}"))
            self.stdout.write(self.style.SUCCESS(f"Lien de restauration rapide mis à jour : {latest_path}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la sauvegarde : {str(e)}"))

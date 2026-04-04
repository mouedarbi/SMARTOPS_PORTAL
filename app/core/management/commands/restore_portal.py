"""
Nom du fichier : restore_portal.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Commande personnalisée pour restaurer l'intégralité des données du portail depuis une fixture.
"""

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Restaure les données du portail depuis la dernière sauvegarde (latest.json)."

    def handle(self, *args, **options):
        latest_path = os.path.join(os.getcwd(), 'backups', 'latest.json')
        
        if not os.path.exists(latest_path):
            self.stdout.write(self.style.ERROR(f"Aucun fichier de sauvegarde trouvé à l'adresse : {latest_path}"))
            return

        self.stdout.write(self.style.WARNING("ATTENTION : Cette opération va écraser les données actuelles."))
        
        try:
            # On charge les données
            call_command('loaddata', latest_path)
            self.stdout.write(self.style.SUCCESS(f"Restauration terminée avec succès depuis {latest_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la restauration : {str(e)}"))

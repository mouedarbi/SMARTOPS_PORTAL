import pluggy
from django.apps import apps
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

hookimpl = pluggy.HookimplMarker("smartops")

class ContractsPlugin:
    """
    Implémentation des hooks pour le module de Gestion des Contrats.
    """

    @hookimpl
    def register_menu_items(self):
        return [{
            "label": "Contrats de Maintenance",
            "url": "/app/contracts/",
            "icon": "la-file-contract"
        }]

    @hookimpl
    def enrich_client_detail_context(self, client, context):
        """
        Ajoute les contrats actifs au contexte de la fiche client.
        """
        try:
            MaintenanceContract = apps.get_model('contracts', 'MaintenanceContract')
            contracts = MaintenanceContract.objects.filter(client_id=client.id, is_active=True)
            context['active_contracts'] = contracts
        except (LookupError, Exception):
            context['active_contracts'] = []

    @hookimpl
    def register_periodic_tasks(self):
        """
        Enregistre la tâche de scan des contrats pour génération de tickets.
        """
        return [
            {
                "name": "generate_contract_tickets",
                "function": self.generate_tickets,
                "frequency": "daily"
            }
        ]

    def generate_tickets(self):
        """
        Logique de scan : 
        1. Trouve les occurrences non générées dans les 30 prochains jours.
        2. Vérifie la charge (optionnel pour l'instant).
        3. Crée un MaintenanceTicket dans le Core avec statut 'pending'.
        """
        from .models import ContractOccurrence
        
        # On cherche ce qui arrive dans 30 jours
        horizon = timezone.now().date() + timedelta(days=30)
        occurrences = ContractOccurrence.objects.filter(
            is_generated=False, 
            planned_date__lte=horizon
        )

        MaintenanceTicket = apps.get_model('maintenance', 'MaintenanceTicket')
        Equipment = apps.get_model('inventory', 'Equipment')

        for occ in occurrences:
            try:
                equipment = Equipment.objects.get(id=occ.contract.equipment_id)
                
                # Création du ticket dans le Core
                ticket = MaintenanceTicket.objects.create(
                    equipment=equipment,
                    type="maintenance",
                    planned_start=timezone.make_aware(timezone.datetime.combine(occ.planned_date, timezone.datetime.min.time())),
                    planned_end=timezone.make_aware(timezone.datetime.combine(occ.planned_date, timezone.datetime.min.time()) + timedelta(hours=2)),
                    status="pending",
                    description=f"Maintenance préventive (Contrat: {occ.contract.name})"
                )
                
                # Mise à jour de l'occurrence
                occ.is_generated = True
                occ.ticket_id = ticket.id
                occ.save()
                
            except Exception as e:
                # Log error
                print(f"Erreur lors de la génération du ticket pour l'occurrence {occ.id}: {e}")

plugin_implementation = ContractsPlugin()

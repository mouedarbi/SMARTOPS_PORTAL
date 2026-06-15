from django.db import models
from django.utils import timezone
from django.apps import apps
from datetime import timedelta

class MaintenanceContract(models.Model):
    """
    Contrat de maintenance liant un client à un équipement spécifique.
    """
    FREQUENCY_CHOICES = [
        (1, "1 visite par an"),
        (2, "2 visites par an"),
        (4, "4 visites par an (Trimestriel)"),
        (12, "12 visites par an (Mensuel)"),
    ]

    # Utilisation de get_model pour la flexibilité (Addon)
    client_id = models.IntegerField(verbose_name="ID Client") # On peut aussi utiliser ForeignKey si on est sûr de l'install
    equipment_id = models.IntegerField(verbose_name="ID Équipement")
    
    name = models.CharField(max_length=255, verbose_name="Nom du contrat")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    
    frequency = models.IntegerField(choices=FREQUENCY_CHOICES, default=1, verbose_name="Fréquence")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contrat de Maintenance"
        verbose_name_plural = "Contrats de Maintenance"

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

class ContractOccurrence(models.Model):
    """
    Échéances prévues pour un contrat.
    Sert de base pour la génération des tickets réels.
    """
    contract = models.ForeignKey(MaintenanceContract, on_delete=models.CASCADE, related_name="occurrences")
    planned_date = models.DateField(verbose_name="Date d'échéance prévue")
    ticket_id = models.IntegerField(null=True, blank=True, verbose_name="ID Ticket généré")
    is_generated = models.BooleanField(default=False, verbose_name="Ticket généré")

    class Meta:
        verbose_name = "Échéance de contrat"
        verbose_name_plural = "Échéances de contrat"
        ordering = ['planned_date']

    def __str__(self):
        return f"Échéance {self.planned_date} pour {self.contract.name}"

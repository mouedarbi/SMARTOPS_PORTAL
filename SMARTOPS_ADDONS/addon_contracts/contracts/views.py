from django.shortcuts import render, redirect
from .models import MaintenanceContract, ContractOccurrence
from django.utils import timezone
from dateutil.relativedelta import relativedelta

def contract_list(request):
    contracts = MaintenanceContract.objects.all().order_by('-created_at')
    return render(request, 'contracts/contract_list.html', {'contracts': contracts})

def create_contract(request):
    # Logique simplifiée pour l'exemple
    if request.method == 'POST':
        # Extraction des données du formulaire...
        pass
    return render(request, 'contracts/contract_form.html')

def generate_occurrences(contract):
    """
    Génère les échéances théoriques pour la durée du contrat.
    """
    current_date = contract.start_date
    months_step = 12 // contract.frequency
    
    while current_date <= contract.end_date:
        ContractOccurrence.objects.create(
            contract=contract,
            planned_date=current_date
        )
        current_date += relativedelta(months=months_step)

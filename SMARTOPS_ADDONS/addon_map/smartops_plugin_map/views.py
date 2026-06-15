from django.shortcuts import render
# Note: Dans un vrai module, nous importerions les modèles du Core SMARTOPS
# via apps.get_model pour éviter les dépendances circulaires ou fortes.
from django.apps import apps

def map_index(request):
    """
    Vue principale du module de cartographie.
    Récupère les sites et les tickets pour les passer à Leaflet.
    """
    # Simulation de données (à remplacer par des requêtes réelles sur le Core)
    # Dans SMARTOPS Core, on utiliserait :
    # Site = apps.get_model('inventory', 'Site')
    # Ticket = apps.get_model('maintenance', 'Ticket')
    
    context = {
        'api_key': 'open-source-leaflet',
    }
    return render(request, 'smartops_plugin_map/index.html', context)

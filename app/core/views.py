"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Contrôleurs pour les pages publiques du Marketplace (Accueil, etc.).
"""

from django.http import HttpResponse

def home_view(request):
    """
    Vue principale servant de point d'entrée au Marketplace.
    
    @param request : L'objet requête HTTP reçu du client.
    @return : Un objet HttpResponse affichant le message de bienvenue.
    """
    return HttpResponse("<h1>Bienvenue sur le Marketplace SMARTOPS !</h1>")

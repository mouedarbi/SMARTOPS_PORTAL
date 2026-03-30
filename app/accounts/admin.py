"""
Fichier : admin.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Configuration de l'interface d'administration pour le modèle User personnalisé.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Configuration du modèle User personnalisé dans l'administration.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Champs à afficher dans la liste des utilisateurs.
    list_display = ('username', 'email', 'language_preference', 'is_client', 'is_staff')
    
    # Ajout de nos champs personnalisés dans le formulaire de modification.
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Marketplace', {'fields': ('language_preference', 'is_client')}),
    )
    
    # Ajout de nos champs personnalisés dans le formulaire de création.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Marketplace', {'fields': ('language_preference', 'is_client')}),
    )

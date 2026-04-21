"""
Fichier : admin.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.2
Description : Administration des licences et des installations clientes.
"""

from django.contrib import admin
from .models import License, Installation

@admin.register(Installation)
class InstallationAdmin(admin.ModelAdmin):
    """
    Monitoring des machines clientes.
    Affiche l'UUID, le propriétaire et la date de synchro.
    """
    list_display = ('installation_uuid', 'user', 'company_name', 'last_sync')
    search_fields = ('installation_uuid', 'user__username', 'company_name')
    list_filter = ('last_sync', 'created_at')

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    """
    Gestion des licences accordées.
    Lien vers le module et l'éventuelle installation liée.
    """
    list_display = ('license_key', 'user', 'module', 'installation', 'is_active')
    search_fields = ('license_key', 'user__username', 'module__name')
    list_filter = ('is_active', 'module')
    readonly_fields = ('license_key', 'created_at')

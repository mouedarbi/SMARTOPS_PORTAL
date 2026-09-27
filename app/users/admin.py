"""
Fichier : admin.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Configuration de l'interface d'administration pour le modèle User personnalisé.
"""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _, ngettext
from .models import User

# Configuration du modèle User personnalisé dans l'administration.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Champs à afficher dans la liste des utilisateurs.
    list_display = ('username', 'email', 'language_preference', 'is_client', 'is_staff', 'is_active', 'is_deleted')
    list_filter = UserAdmin.list_filter + ('is_client', 'is_deleted')
    actions = ['anonymize_accounts']
    
    # Ajout de nos champs personnalisés dans le formulaire de modification.
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Marketplace', {'fields': ('language_preference', 'is_client')}),
    )
    
    # Ajout de nos champs personnalisés dans le formulaire de création.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Marketplace', {'fields': ('language_preference', 'is_client')}),
    )

    def has_delete_permission(self, request, obj=None):
        # Un compte lié à des commandes ou licences n'est jamais supprimé physiquement :
        # il est anonymisé (commandes et licences conservées, §9.5 du rapport).
        if obj is not None and (obj.orders.exists() or obj.licenses.exists()):
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description=_("Anonymiser les comptes sélectionnés (RGPD)"), permissions=['change'])
    def anonymize_accounts(self, request, queryset):
        users = [u for u in queryset if not u.is_deleted and not u.is_superuser]
        for user in users:
            user.anonymize()
        self.message_user(request, ngettext(
            "%d compte anonymisé ; commandes et licences conservées.",
            "%d comptes anonymisés ; commandes et licences conservées.",
            len(users),
        ) % len(users), messages.SUCCESS)


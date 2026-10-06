"""
Fichier : admin.py
Projet : Marketplace SMARTOPS
Application : accounts
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Configuration de l'interface d'administration pour le modèle User personnalisé.
"""

import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _, ngettext
from .models import User

audit_logger = logging.getLogger('audit')

# Configuration du modèle User personnalisé dans l'administration.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Administration des comptes clients, journalisée, avec anonymisation RGPD."""
    # Champs à afficher dans la liste des utilisateurs.
    list_display = ('username', 'email', 'account_type', 'language_preference', 'is_client', 'is_staff', 'is_active', 'is_deleted')
    list_filter = UserAdmin.list_filter + ('is_client', 'account_type', 'is_deleted')
    readonly_fields = ('account_type',)
    actions = ['anonymize_accounts']
    
    # Ajout de nos champs personnalisés dans le formulaire de modification.
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Marketplace', {'fields': ('language_preference', 'is_client', 'account_type')}),
    )
    
    # Ajout de nos champs personnalisés dans le formulaire de création.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Marketplace', {'fields': ('language_preference', 'is_client')}),
    )

    def save_model(self, request, obj, form, change):
        """Enregistre le compte et journalise la création ou les champs modifiés."""
        super().save_model(request, obj, form, change)
        action = "ADMIN ACCOUNT UPDATE" if change else "ADMIN ACCOUNT CREATE"
        fields = ', '.join(f for f in form.changed_data if 'password' not in f) or '-'
        audit_logger.info(
            f"{action}: User {obj.username} (ID: {obj.pk}) by {request.user.username}. Fields: {fields}."
        )

    def delete_model(self, request, obj):
        """Journalise puis supprime le compte."""
        audit_logger.info(f"ADMIN ACCOUNT DELETE: User {obj.username} (ID: {obj.pk}) deleted by {request.user.username}.")
        super().delete_model(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Interdit la suppression d'un compte lié à des commandes ou licences."""
        # Un compte lié à des commandes ou licences n'est jamais supprimé physiquement :
        # il est anonymisé (commandes et licences conservées, §9.5 du rapport).
        if obj is not None and (obj.orders.exists() or obj.licenses.exists()):
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description=_("Anonymiser les comptes sélectionnés (RGPD)"), permissions=['change'])
    def anonymize_accounts(self, request, queryset):
        """Anonymise les comptes sélectionnés (commandes et licences conservées)."""
        users = [u for u in queryset if not u.is_deleted and not u.is_superuser]
        for user in users:
            audit_logger.info(
                f"ADMIN ACCOUNT ANONYMIZED: User {user.username} (ID: {user.pk}) anonymized by {request.user.username} "
                f"(orders and licenses kept)."
            )
            user.anonymize()
        self.message_user(request, ngettext(
            "%d compte anonymisé ; commandes et licences conservées.",
            "%d comptes anonymisés ; commandes et licences conservées.",
            len(users),
        ) % len(users), messages.SUCCESS)

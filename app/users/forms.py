"""
Fichier : forms.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Formulaires de compte personnalisés (django-allauth).
"""

from allauth.account.forms import ResetPasswordForm
from django import forms
from django.contrib.auth import get_user_model

from .models import BillingProfile, normalize_belgian_vat
from .signup_forms import BILLING_FIELDS, widen_vat_field


class FrozenAccountAwareResetPasswordForm(ResetPasswordForm):
    """Mot de passe oublié : aucun e-mail n'est envoyé à l'adresse d'un compte supprimé.

    Pendant le délai de grâce avant anonymisation, le compte est gelé. allauth le traite comme
    inconnu (il est inactif) et enverrait à son adresse l'e-mail « compte inconnu » : on ne
    l'envoie pas. La page affichée reste la même, sans rien révéler sur le compte.
    """

    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]
        if not self.users and get_user_model().objects.filter(email__iexact=email, is_deleted=True).exists():
            return email
        return super().save(request, **kwargs)


class BillingProfileForm(forms.ModelForm):
    """Coordonnées de facturation d'un compte professionnel (entreprise établie en Belgique)."""

    class Meta:
        model = BillingProfile
        fields = BILLING_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widen_vat_field(self.fields['vat_number'])

    def clean_vat_number(self):
        return normalize_belgian_vat(self.cleaned_data['vat_number'])

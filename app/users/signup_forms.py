"""
Fichier : signup_forms.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Champs ajoutés au formulaire d'inscription allauth (ACCOUNT_SIGNUP_FORM_CLASS).
              Module séparé de forms.py : allauth le charge pendant l'import de
              allauth.account.forms, il ne doit donc pas importer ce module.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import BillingProfile, User

BILLING_FIELDS = ('company_name', 'vat_number', 'street', 'postal_code', 'city')


def vat_placeholder(field):
    """Numéro de TVA en saisie libre : l'exemple guide le client sans rien imposer."""
    field.widget.attrs['placeholder'] = 'BE0123456789'


class SignupForm(forms.Form):
    """Champs ajoutés à l'inscription allauth (ACCOUNT_SIGNUP_FORM_CLASS).

    Le type de compte est choisi une fois pour toutes. Un compte professionnel doit fournir les
    coordonnées de son entreprise, établie en Belgique.
    """
    account_type = forms.ChoiceField(
        label=_("Type de compte"),
        choices=User.ACCOUNT_TYPES,
        initial='individual',
        required=False,
        widget=forms.RadioSelect,
        help_text=_("Ce choix est définitif : un compte particulier ne peut pas devenir professionnel, "
                    "ni l'inverse."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in forms.fields_for_model(BillingProfile, fields=BILLING_FIELDS).items():
            field.required = False
            self.fields[name] = field
        vat_placeholder(self.fields['vat_number'])

    def clean(self):
        """
        Type de compte par défaut « particulier » ; coordonnées de facturation
        obligatoires pour un compte professionnel.
        """
        cleaned = super().clean()
        cleaned['account_type'] = cleaned.get('account_type') or 'individual'
        if cleaned['account_type'] == 'professional':
            for name in BILLING_FIELDS:
                if not cleaned.get(name):
                    self.add_error(name, _("Ce champ est obligatoire pour un compte professionnel."))
        return cleaned

    def signup(self, request, user):
        """Enregistre le type de compte et, pour un professionnel, son profil de facturation."""
        user.account_type = self.cleaned_data['account_type']
        user.save(update_fields=['account_type'])
        if user.is_professional:
            BillingProfile.objects.create(user=user, **{name: self.cleaned_data[name] for name in BILLING_FIELDS})

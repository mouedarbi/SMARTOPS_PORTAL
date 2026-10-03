"""
Fichier : signup_forms.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Champs ajoutés au formulaire d'inscription allauth (ACCOUNT_SIGNUP_FORM_CLASS).
              Module séparé de forms.py : allauth le charge pendant l'import de
              allauth.account.forms, il ne doit donc pas importer ce module.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from .models import BillingProfile, User, normalize_belgian_vat

BILLING_FIELDS = ('company_name', 'vat_number', 'street', 'postal_code', 'city')


def widen_vat_field(field):
    """Accepte la saisie libre (« BE 0123.456.749 ») ; la valeur normalisée tient en 12 caractères."""
    field.max_length = 20
    field.validators = [v for v in field.validators if not isinstance(v, MaxLengthValidator)]
    field.widget.attrs['maxlength'] = '20'
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
        widen_vat_field(self.fields['vat_number'])

    def clean(self):
        cleaned = super().clean()
        cleaned['account_type'] = cleaned.get('account_type') or 'individual'
        if cleaned['account_type'] == 'professional':
            for name in BILLING_FIELDS:
                if not cleaned.get(name):
                    self.add_error(name, _("Ce champ est obligatoire pour un compte professionnel."))
            if cleaned.get('vat_number'):
                try:
                    cleaned['vat_number'] = normalize_belgian_vat(cleaned['vat_number'])
                except ValidationError as error:
                    self.add_error('vat_number', error)
        return cleaned

    def signup(self, request, user):
        user.account_type = self.cleaned_data['account_type']
        user.save(update_fields=['account_type'])
        if user.is_professional:
            BillingProfile.objects.create(user=user, **{name: self.cleaned_data[name] for name in BILLING_FIELDS})

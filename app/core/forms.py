"""
Fichier : forms.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Description : Formulaire de contact de la page d'accueil.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120)
    email = forms.EmailField()
    message = forms.CharField(max_length=5000)

    def clean_message(self):
        message = (self.cleaned_data.get("message") or "").strip()
        if len(message) < 5:
            raise forms.ValidationError(_("Message trop court."))
        return message

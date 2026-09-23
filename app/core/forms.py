"""
Fichier : forms.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Description : Formulaire de contact de la page d'accueil.
"""

from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]

    def clean_message(self):
        message = (self.cleaned_data.get("message") or "").strip()
        if len(message) < 5:
            raise forms.ValidationError("Message trop court.")
        return message

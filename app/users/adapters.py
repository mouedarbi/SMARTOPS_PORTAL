"""
Fichier : adapters.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Adaptateur allauth : journalisation des e-mails de compte, redirection et message
              après la déconnexion.
"""

import logging

from allauth.account.adapter import DefaultAccountAdapter

audit_logger = logging.getLogger('audit')

class CustomAccountAdapter(DefaultAccountAdapter):
    """Adaptateur allauth du Portal."""
    def get_client_ip(self, request):
        """Adresse IP du client derrière nginx."""
        # Récupération sécurisée de l'IP derrière Nginx
        ip = request.META.get('HTTP_X_REAL_IP') or \
             request.META.get('HTTP_X_FORWARDED_FOR') or \
             request.META.get('REMOTE_ADDR')

        if not ip:
            return '127.0.0.1' # Évite le crash 403 si l'IP est indéterminée

        return ip.split(',')[0].strip()

    def send_password_reset_mail(self, user, email, context):
        """Journalise l'envoi du lien de réinitialisation du mot de passe."""
        audit_logger.info(
            f"PASSWORD RESET REQUESTED: Reset link sent to {email} for user {user.username} (ID: {user.pk})."
        )
        return super().send_password_reset_mail(user, email, context)

    def send_mail(self, template_prefix, email, context):
        """Envoie l'e-mail et journalise un éventuel échec d'envoi."""
        try:
            return super().send_mail(template_prefix, email, context)
        except Exception as e:
            audit_logger.error(f"EMAIL SEND FAILED: Template {template_prefix} to {email}. Error: {e}")
            raise

    def get_logout_redirect_url(self, request):
        """Après la déconnexion : retour à l'accueil."""
        from django.urls import reverse
        return reverse('core:home')

    def add_message(
        self,
        request,
        level,
        message_template=None,
        message_context=None,
        extra_tags="",
        message=None,
    ):
        """Messages allauth, sauf « Vous êtes déconnecté »."""
        if message_template == "account/messages/logged_out.txt":
            return
        super().add_message(
            request,
            level,
            message_template=message_template,
            message_context=message_context,
            extra_tags=extra_tags,
            message=message,
        )

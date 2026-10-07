"""
Fichier : emails.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Envoi des e-mails transactionnels au client, dans sa langue préférée : sujet,
              texte et HTML rendus depuis templates/<prefix>_subject.txt, _message.txt et
              _message.html. Un échec d'envoi est journalisé sans interrompre l'opération
              qui l'a déclenché.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation

audit_logger = logging.getLogger('audit')


def customer_language(user):
    """Langue préférée du client, ou le français si elle n'est pas proposée par le site."""
    return user.language_preference if user.language_preference in dict(settings.LANGUAGES) else 'fr'


def send_customer_email(user, template_prefix, request, build_context=None, log_label=''):
    """Envoie un e-mail au client ; True s'il est parti.

    build_context(request) est appelée dans la langue du client et renvoie le contexte des
    templates et les pièces jointes : (context, [(nom, contenu, type MIME), ...]).
    """
    if not user.email:
        return False
    language = customer_language(user)
    try:
        with translation.override(language):
            context, attachments = build_context(request) if build_context else ({}, [])
            context = {'user': user,
                       'dashboard_url': request.build_absolute_uri(reverse('users:dashboard')),
                       **context}
            subject = settings.ACCOUNT_EMAIL_SUBJECT_PREFIX + ' '.join(
                render_to_string(f'{template_prefix}_subject.txt', context).split())
            message = EmailMultiAlternatives(
                subject=subject,
                body=render_to_string(f'{template_prefix}_message.txt', context),
                to=[user.email],
            )
            message.attach_alternative(render_to_string(f'{template_prefix}_message.html', context), 'text/html')
            for attachment in attachments:
                message.attach(*attachment)
            message.send()
    except Exception:
        audit_logger.exception(f"EMAIL FAILED: {template_prefix} {log_label} (user ID {user.pk}).")
        return False
    audit_logger.info(f"EMAIL SENT: {template_prefix} {log_label} to user ID {user.pk} (language {language}).")
    return True

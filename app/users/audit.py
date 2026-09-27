"""
Fichier : audit.py
Projet : Marketplace SMARTOPS
Application : users
Description : Journalisation des événements de compte dans le journal applicatif (logs/audit.log),
              consultable dans le back-office. Les mots de passe ne sont jamais journalisés.
"""

import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from allauth.account.signals import (
    email_changed, password_changed, password_reset, password_set, user_signed_up,
)

audit_logger = logging.getLogger('audit')


def client_ip(request):
    """IP du client derrière nginx (X-Real-IP), à défaut REMOTE_ADDR."""
    if request is None:
        return '-'
    meta = request.META
    ip = meta.get('HTTP_X_REAL_IP') or meta.get('HTTP_X_FORWARDED_FOR') or meta.get('REMOTE_ADDR') or '-'
    return ip.split(',')[0].strip()


def describe(user):
    return f"{user.username} (ID: {user.pk})"


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    audit_logger.info(f"AUTH LOGIN SUCCESS: User {describe(user)} from IP {client_ip(request)}.")


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request=None, **kwargs):
    # Django masque déjà le mot de passe ; seul l'identifiant saisi est repris.
    login = credentials.get('email') or credentials.get('username') or credentials.get('login') or '-'
    audit_logger.warning(f"AUTH LOGIN FAILED: Identifier '{login}' from IP {client_ip(request)}.")


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user is not None:
        audit_logger.info(f"AUTH LOGOUT: User {describe(user)} from IP {client_ip(request)}.")


@receiver(user_signed_up)
def log_signup(sender, request, user, **kwargs):
    audit_logger.info(f"ACCOUNT SIGNUP SUCCESS: User {describe(user)} created from IP {client_ip(request)}.")


@receiver(password_reset)
def log_password_reset(sender, request, user, **kwargs):
    audit_logger.info(f"PASSWORD RESET SUCCESS: User {describe(user)} set a new password from IP {client_ip(request)}.")


@receiver(password_changed)
def log_password_changed(sender, request, user, **kwargs):
    audit_logger.info(f"PASSWORD CHANGE SUCCESS: User {describe(user)} from IP {client_ip(request)}.")


@receiver(password_set)
def log_password_set(sender, request, user, **kwargs):
    audit_logger.info(f"PASSWORD SET SUCCESS: User {describe(user)} from IP {client_ip(request)}.")


@receiver(email_changed)
def log_email_changed(sender, request, user, from_email_address=None, to_email_address=None, **kwargs):
    audit_logger.info(
        f"ACCOUNT UPDATE: User {describe(user)} changed email from "
        f"{getattr(from_email_address, 'email', '-')} to {getattr(to_email_address, 'email', '-')}."
    )

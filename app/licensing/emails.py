"""
Fichier : emails.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : E-mails envoyés au client quand une de ses licences est activée sur une installation
              SMARTOPS Core ou libérée de celle-ci, pour qu'il repère tout usage non autorisé de
              ses clés.
"""

from django.utils import timezone

from users.emails import send_customer_email


def _installation_label(installation):
    """Nom de l'entreprise déclaré par l'installation Core, suivi de son identifiant."""
    if installation.company_name:
        return f"{installation.company_name} ({installation.installation_uuid})"
    return str(installation.installation_uuid)


def _send(license_obj, installation, request, template):
    context = {
        'license': license_obj,
        'key_end': str(license_obj.license_key)[-8:],
        'installation': _installation_label(installation),
        'event_at': timezone.now(),
    }
    return send_customer_email(license_obj.user, f'licensing/email/{template}', request,
                               lambda request: (context, []), log_label=f"License #{license_obj.pk}")


def send_license_activated(license_obj, installation, request):
    """Prévient le client de la première activation de sa licence sur une installation."""
    return _send(license_obj, installation, request, 'license_activated')


def send_license_released(license_obj, installation, request):
    """Prévient le client que sa licence a été libérée de son installation."""
    return _send(license_obj, installation, request, 'license_released')

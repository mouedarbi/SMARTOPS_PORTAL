"""
Fichier : anonymize_deleted_accounts.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Anonymise les comptes supprimés par leur titulaire une fois le délai de grâce
              écoulé (ACCOUNT_ANONYMIZATION_DELAY_DAYS depuis deleted_at). Planifiée une fois
              par jour (crontab, voir README). Idempotente : un compte déjà anonymisé (e-mail
              en ANONYMIZED_EMAIL_DOMAIN) n'est plus jamais sélectionné. Les commandes et
              licences ne sont pas touchées (Art. 17.3.b RGPD).
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import ANONYMIZED_EMAIL_DOMAIN

audit_logger = logging.getLogger('audit')


class Command(BaseCommand):
    """Commande « anonymize_deleted_accounts »."""
    help = "Anonymise les comptes supprimés depuis plus de ACCOUNT_ANONYMIZATION_DELAY_DAYS jours."

    def add_arguments(self, parser):
        """Option --dry-run."""
        parser.add_argument('--dry-run', action='store_true',
                            help="Liste les comptes concernés sans les modifier.")

    def handle(self, *args, dry_run=False, **options):
        """Anonymise les comptes supprimés depuis plus que le délai prévu (ou les liste)."""
        delay = settings.ACCOUNT_ANONYMIZATION_DELAY_DAYS
        users = (get_user_model().objects
                 .filter(is_deleted=True, deleted_at__lte=timezone.now() - timedelta(days=delay))
                 .exclude(email__endswith=ANONYMIZED_EMAIL_DOMAIN)
                 .order_by('deleted_at'))
        count = 0
        for user in users:
            # Identifiant interne et date de la demande uniquement : aucune donnée personnelle.
            if dry_run:
                self.stdout.write(f"[dry-run] Compte ID {user.pk} supprimé le {user.deleted_at:%Y-%m-%d} : à anonymiser.")
            else:
                user.anonymize()
                audit_logger.info(
                    f"ACCOUNT ANONYMIZED: User ID {user.pk} anonymized by scheduled task "
                    f"(deletion requested on {user.deleted_at:%Y-%m-%d}, delay {delay} days)."
                )
            count += 1
        verb = "à anonymiser" if dry_run else "anonymisé(s)"
        self.stdout.write(f"{timezone.now():%Y-%m-%d %H:%M:%S} UTC : {count} compte(s) {verb} (délai : {delay} jours).")

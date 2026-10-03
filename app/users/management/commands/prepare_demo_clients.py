"""
Fichier : prepare_demo_clients.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Convertit les clients fictifs existants (adresses @example.be) en comptes de
              démonstration : adresse opensmartops+userN@gmail.com (plus addressing) et
              répartition 70 % professionnels / 30 % particuliers, avec coordonnées
              d'entreprise fictives. Ne touche à aucun autre compte (admin, comptes réels, de
              test, supprimés). Idempotente : une fois convertis, plus aucun compte ne correspond.
"""

import random

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from users.demo_data import demo_email, fictitious_company, is_professional_slot
from users.models import BillingProfile

FICTITIOUS_DOMAIN = '@example.be'


class Command(BaseCommand):
    help = "Convertit les clients fictifs @example.be en comptes de démonstration (Gmail plus addressing, 70 % pro)."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Affiche les conversions sans rien modifier.")

    def handle(self, *args, dry_run=False, **options):
        User = get_user_model()
        users = list(User.objects
                     .filter(email__endswith=FICTITIOUS_DOMAIN, is_deleted=False, is_staff=False, is_superuser=False)
                     .order_by('pk'))
        used = set(User.objects.filter(email__startswith='opensmartops+user').values_list('email', flat=True))
        number, pros = 0, 0
        with transaction.atomic():
            for index, user in enumerate(users):
                number += 1
                while demo_email(number) in used:
                    number += 1
                email = demo_email(number)
                professional = is_professional_slot(index)
                pros += professional
                kind = 'pro' if professional else 'particulier'
                self.stdout.write(f"{'[dry-run] ' if dry_run else ''}ID {user.pk} -> {email} ({kind})")
                if dry_run:
                    continue
                EmailAddress.objects.filter(user=user).update(email=email)
                user.email = email
                user.account_type = 'professional' if professional else 'individual'
                user.save(update_fields=['email', 'account_type'])
                if professional:
                    rng = random.Random(user.pk)
                    BillingProfile.objects.update_or_create(
                        user=user, defaults=fictitious_company(rng, user.first_name, user.last_name))
            if dry_run:
                transaction.set_rollback(True)
        self.stdout.write(f"{len(users)} compte(s) {'à convertir' if dry_run else 'converti(s)'} : "
                          f"{pros} professionnel(s), {len(users) - pros} particulier(s).")

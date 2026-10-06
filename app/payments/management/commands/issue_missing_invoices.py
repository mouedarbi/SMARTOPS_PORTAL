"""
Fichier : issue_missing_invoices.py
Projet : Marketplace SMARTOPS
Application : payments
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Émet les factures manquantes des commandes payées de comptes professionnels
              (commandes antérieures aux factures, ou émission échouée), datées du jour de la
              commande et numérotées dans l'ordre chronologique. Idempotente.
"""

from django.core.management.base import BaseCommand

from payments.invoicing import issue_missing_invoices


class Command(BaseCommand):
    """Commande « issue_missing_invoices »."""
    help = "Émet les factures manquantes des commandes payées de comptes professionnels."

    def handle(self, *args, **options):
        """Émet les factures manquantes et affiche leur numéro."""
        invoices = issue_missing_invoices()
        for invoice in invoices:
            self.stdout.write(f"{invoice.number} : commande #{invoice.order_id}")
        self.stdout.write(f"{len(invoices)} facture(s) émise(s).")

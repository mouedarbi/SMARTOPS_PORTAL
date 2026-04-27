# Plan de Travail - Mardi 28 Avril 2026

## 1. Seeders & Data Generation (Exigence Professeur)
- Créer une commande de management Django : `python manage.py seed_data`.
- Générer **100 utilisateurs** (Format : `Jean` / Pass : `jean123`).
- Générer des données cohérentes pour les tables : `Modules`, `Categories`, `Transactions`.
- Objectif : 100 enregistrements minimum par table pour tests de performance UI.

## 2. Intégrité des Données & Soft Delete
- Implémenter le concept de **Soft Delete** (champ `deleted_at`) sur les modèles critiques :
    - `User`
    - `Module`
    - `Order`
- Tester la suppression en cascade vs soft delete pour garantir qu'aucune donnée comptable ou de licence n'est perdue.

## 3. Conformité RGPD / GDPR
- Créer une fonctionnalité permettant à l'utilisateur de demander la suppression de ses données.
- Implémenter la logique d'**Anonymisation** (garder la transaction pour la compta, mais effacer nom/email).

## 4. Audit & Logs
- Vérifier et renforcer la journalisation des actions administratives sensibles.
- Préparer une démonstration pour le professeur montrant la traçabilité des données.

# Stratégie de Refonte SMARTOPS PORTAL

## Objectif
Passer d'une architecture lourde basée sur Wagtail CMS (~100 tables) à une architecture Django "Pure Dev" ultra-légère, afin de mettre en avant le code personnel et de simplifier la maintenance.

## Architecture Cible
- **Framework** : Django 6.0
- **Authentification** : Django Allauth (Conservé)
- **Traduction** : `django-modeltranslation` (pour les modèles) et `i18n` standard (pour les templates).
- **Base de données** : SQLite (Schéma réduit à ~20 tables).

## Étapes de la Refonte

### Étape 1 : Nettoyage et Branchement
- Création de la branche `refonte-schema`.
- Documentation de l'inventaire actuel.

### Étape 2 : Recréation de la Home Page (Hardcoded)
- Création d'une vue Django classique dans `core/views.py`.
- Création d'un template `templates/pages/home.html` reprenant le design actuel mais avec le contenu en dur (HTML).
- Intégration des statistiques GitHub via la fonction python existante.
- Affichage des modules et packs "Featured" directement depuis les modèles `catalog`.

### Étape 3 : Migration du Catalogue (Modèles Métiers)
- Transformation de `catalog/models.py` :
    - Remplacement de `TranslatableMixin` par `models.Model`.
    - Remplacement des `ParentalKey` par des `ForeignKey`.
    - Suppression de toute référence à `wagtail`.
- Configuration de `translation.py` pour activer le multilingue sur `name`, `description`, etc.

### Étape 4 : Système de Traduction des Templates
- Marquage des textes de la Home Page avec `{% trans %}`.
- Génération des fichiers `.po` pour FR, EN, NL.

### Étape 5 : Suppression définitive de Wagtail
- Retrait des apps `wagtail` dans `settings.py`.
- Nettoyage du `requirements.txt`.
- Suppression des tables Wagtail dans la DB.

---
**Responsable** : Mohamed Ouedarbi
**Version** : 1.0

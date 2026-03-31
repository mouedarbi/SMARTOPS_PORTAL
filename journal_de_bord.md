# Journal de Bord - Projet Marketplace SMARTOPS

---

## [16/03/2026] - Initialisation et Configuration du Socle

### Problème : Conflit de port au démarrage du serveur
- **Description** : Port 5000 déjà utilisé par un autre processus.
- **Solution** : Utilisation du port 8001 : `python3 manage.py runserver 8001`.

### Problème : Standards de documentation académiques
- **Description** : Absence de documentation structurée dans les fichiers générés par défaut.
- **Solution** : Réécriture des en-têtes et des docstrings selon les standards industriels (Auteur, Version, @param, @return).

### Problème : Sécurisation de l'accès administratif
- **Description** : Besoin de valider l'accès au panneau d'administration.
- **Solution** : Création d'un super-utilisateur via le shell Django pour tester l'authentification.

---

## [30/03/2026] - Architecture Modulaire et Modèle Utilisateur

### Avancement : Mise en place de l'architecture modulaire
- **Description** : Création et configuration des applications socles du Marketplace : `accounts`, `catalog`, `payments`, `licensing`, `downloads` et `content`.
- **Outcome** : Structure globale du projet finalisée avec routage d'URL opérationnel pour chaque module.

### Problème : Conflit d'historique de migrations (InconsistentMigrationHistory)
- **Description** : L'implémentation tardive du modèle User personnalisé a généré un conflit avec l'historique des migrations initiales de Django.
- **Solution** : Réinitialisation de la base de données de développement (`db.sqlite3`) pour intégrer le nouveau schéma `accounts.User` de manière propre et pérenne.
- **Outcome** : Base de données synchronisée avec le modèle utilisateur personnalisé incluant les préférences linguistiques.

---

## [30/03/2026] - Intégration de l'Authentification (RAD)

### Avancement : Intégration de django-allauth
- **Description** : Mise en place de la brique d'authentification RAD pour la gestion des membres.
- **Implementation** : Installation de `django-allauth`, configuration des backends dans `settings.py` et gestion des URLs d'authentification.
- **Problème : Dépréciation de réglages allauth** : Des avertissements sont apparus concernant les anciennes méthodes de configuration.
- **Solution : Mise à jour de la configuration** : Migration vers les nouveaux paramètres recommandés par la version 65.15.0+ de `allauth`.
- **Tests** : Création d'une suite de tests dans `accounts/tests.py` validant l'inscription, la connexion fonctionnelle et la gestion des sessions.
- **Outcome** : Module d'authentification validé par des tests unitaires (4 tests réussis).

---

## [31/03/2026] - Intégration de la Gestion de Contenu (RAD)

### Avancement : Intégration de Wagtail CMS
- **Description** : Mise en place de Wagtail CMS (v7.3.1) pour la gestion dynamique du contenu (Blog, Documentation).
- **Implementation** :
    - Installation des dépendances (wagtail, wagtail-localize).
    - Configuration de INSTALLED_APPS, MIDDLEWARE et des dossiers média dans settings.py.
    - Création des modèles ContentIndexPage et ContentPage dans l'application content.
    - Migration de la base de données (Application de 100+ migrations Wagtail).
    - Routage multilingue via i18n_patterns.

### Problème : Avertissement de configuration allauth (W001)
- **Description** : Conflit détecté entre ACCOUNT_LOGIN_METHODS et ACCOUNT_SIGNUP_FIELDS suite aux mises à jour de django-allauth 65.15.0+.
- **Solution** : Utilisation du suffixe '*' (ex: 'email*', 'username*') dans ACCOUNT_SIGNUP_FIELDS pour marquer explicitement les champs obligatoires à l'inscription, ce qui a supprimé l'avertissement W001.

### Problème : ModuleNotFoundError: No module named 'wagtail_localize.middleware'
- **Description** : Tentative d'utilisation d'un middleware inexistant dans le package `wagtail-localize`.
- **Solution** : Suppression de la ligne fautive dans `settings.py`. La localisation est gérée nativement par le `LocaleMiddleware` de Django et les hooks de Wagtail Localize.
- **Outcome** : Serveur opérationnel sur le port 8001.

---
- 2026-03-31 : Implémentation des modèles catalog (Module, Category, Version, Compatibility) et intégration Wagtail Snippets.

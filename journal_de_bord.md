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

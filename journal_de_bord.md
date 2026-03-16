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

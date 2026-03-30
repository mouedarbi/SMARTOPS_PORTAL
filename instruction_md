Instructions pour le LLM codeur — Projet Marketplace SMARTOPS

1. Objectif du projet
Développer une Marketplace Web professionnelle pour les modules SMARTOPS en utilisant une approche RAD (Rapid Application Development). L'objectif est d'intégrer des solutions existantes robustes pour les fonctionnalités standards et de se concentrer sur le code métier spécifique (licensing).

2. Architecture technique et Stratégie RAD
Pour ne pas réinventer la roue, les choix techniques suivants sont imposés :
- Backend : Django (Python)
- Gestion de Contenu (CMS) : Wagtail CMS (Installation via pip)
- Authentification & Comptes : django-allauth (Installation via pip)
- Paiements : Stripe SDK (Installation via pip)
- Multilingue : Django i18n + Wagtail Localize (Minimum 2 langues : FR/EN)
- Frontend : Tailwind CSS + Alpine.js (pour une interface moderne et réactive)
- Base de données : SQLite (Dev), PostgreSQL (Prod)

3. Structure du serveur cible
Le Marketplace sera déployé via Docker avec une structure claire séparant le code, la configuration (.env) et les volumes (media, static, modules).

4. Règle de développement et Intégration
Le développement est incrémental. Chaque étape consiste soit en l'implémentation de code métier, soit en l'intégration et la configuration d'un progiciel tiers.
Chaque étape doit :
- Implémenter/Intégrer une seule fonctionnalité.
- Produire un commit clair.
- Documenter l'étape dans le journal de bord (technique uniquement).

5. Apps Django et Responsabilités (Programmation par Intégration)
- core : Pages publiques et structure globale du site.
- accounts : Modèle User personnalisé intégré avec django-allauth.
- catalog : Catalogue des modules (code métier).
- payments : Gestion des transactions via Stripe SDK.
- licensing : Serveur de licences et validation API (code métier coeur).
- downloads : Service de téléchargement sécurisé.
- content : Gestion du contenu dynamique (Blog, Doc) via Wagtail CMS.

6. Workflow Multilingue
Le système doit supporter nativement le multilingue :
- Détection de la langue via l'URL ou la préférence utilisateur.
- Traduction des interfaces via les fichiers .po/.mo.
- Traduction des pages CMS via l'interface de gestion Wagtail.

7. Ordre de développement révisé (Stratégie RAD)
Étape 1 : Initialisation et socle technique (Terminé).
Étape 2 : Création des squelettes d'applications (Terminé).
Étape 3 : Configuration du modèle User personnalisé et i18n (Terminé).
Étape 4 : Intégration de django-allauth (Authentification RAD).
Étape 5 : Intégration de Wagtail CMS dans l'app 'content' (Gestion de contenu RAD).
Étape 6 : Développement du Catalogue de modules (Métier).
Étape 7 : Intégration de Stripe dans l'app 'payments' (Paiement RAD).
Étape 8 : Développement du moteur de Licensing et API (Métier).
Étape 9 : Système de téléchargement sécurisé.
Étape 10 : Finalisation UI avec Tailwind CSS & Alpine.js.
Étape 11 : Dockerisation et préparation production.

8. Contraintes de Qualité
- Documentation : En-tête académique obligatoire dans chaque fichier.
- Sécurité : Ne jamais commiter de clés API ou secrets.
- Maintenance : Code modulaire pour faciliter les mises à jour des librairies tierces.

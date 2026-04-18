# État d'avancement - Marketplace SMARTOPS

Ce document permet de suivre la progression du développement par rapport au plan initial de 12 étapes (révisé pour la stratégie RAD).

---

## 1. État des Étapes (Stratégie RAD)

| Étape | Description | État | Détails |
| :--- | :--- | :--- | :--- |
| **1** | **Initialisation et socle technique** | **Terminé** | Django, SQLite, super-utilisateur, configuration de base. |
| **2** | **Création des squelettes d'applications** | **Terminé** | `core`, `accounts`, `catalog`, `payments`, `licensing`, `downloads`, `content` créés. |
| **3** | **Configuration du modèle User & i18n** | **Terminé** | Modèle User personnalisé avec préférences linguistiques. |
| **4** | **Intégration de django-allauth** | **Terminé** | Authentification RAD (Inscription/Connexion) opérationnelle et testée. |
| **5** | **Intégration de Wagtail CMS** | **Terminé** | Gestion de contenu RAD (Blog, Doc) configurée et HomePage pro (Design Landing Page). |
| **6** | **Développement du Catalogue** | **Terminé** | Modèles métier pour les modules (Pay-once) et les packs groupés. |
| **7** | **Intégration de Stripe** | À faire | Paiement RAD via Stripe SDK. |
| **8** | **Moteur de Licensing et API** | À faire | Développement métier du coeur de validation. |
| **9** | **Système de téléchargement** | À faire | Accès sécurisé aux modules achetés. |
| **10** | **UI avec Tailwind & Alpine.js** | À faire | Finalisation esthétique et interactive. |
| **11** | **Dockerisation** | À faire | Préparation pour la production. |

---

## 2. Travail réalisé (Résumé)

- **Socle technique** : Django 6.x, django-allauth (auth sécurisée), Wagtail CMS 7.3.1 (gestion de contenu).
- **Authentification** : Gestion par email, modèle utilisateur étendu, tests validés, résolution du conflit W001.
- **Gestion de Contenu** : 
    - Administration Wagtail sécurisée sur `/portal-management/`.
    - HomePage dynamique avec design professionnel (Terminal, Stats, Marketplace, GitHub).
    - Support multilingue (FR/EN) actif via i18n_patterns.
- **Documentation** : Journal de bord à jour, en-têtes académiques présents, 4 commits atomiques réalisés et poussés.

---

## 3. Prochaines Actions (Prochaine session)

1. Développer l'application `catalog` (Étape 6) : Créer les modèles `Module` et `ModuleBundle`.
2. Implémenter la logique de prix fixe (Pay-once) et de réduction par pack.
3. Lier les données métier `catalog` à l'affichage Wagtail via des Snippets ou des Custom Blocks.

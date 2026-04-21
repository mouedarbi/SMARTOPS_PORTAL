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

## 2026-03-31 : Étape 6 - Développement complet du Catalogue

### Travaux réalisés :
- **Modélisation technique** : Création des modèles Module, Category, CoreVersion (compatibilité), ModuleVersion et ModuleScreenshot.
- **Système de Packs (Bundles)** : Implémentation du modèle ModuleBundle avec calcul automatique du prix final (Remise % ou Prix fixe) et gestion de la validité temporelle (start_date / end_date).
- **Intégration Wagtail** : Tous les modèles sont administrables via les Snippets.
- **Dynamisation UI** : Home Page (modules et packs), Liste du Catalogue avec filtres et Page Détails Module.

### Problèmes rencontrés et Résolutions :
1. **Erreur de port (OverflowError)** : Tentative de démarrage sur le port 80001.
   - *Résolution* : Utilisation du port 8001.
2. **Erreur d'attribut Django (CheckboxSelectMultiple)** : Import erroné depuis models.
   - *Résolution* : Import corrigé depuis django.forms.
3. **Packs non affichés** : Date de début dans le futur (Octobre 2026).
   - *Résolution* : Correction de la date dans l'admin.

---

## [03/04/2026] - Internationalisation et UX Avancée

### Avancement : Finalisation du Système Multilingue (FR, EN, NL)
- **Description** : Mise en place complète du support multilingue pour le portail, incluant le CMS (Wagtail), les briques de données (Snippets) et l'interface utilisateur.
- **Implementation** :
    - Configuration des 3 langues : Français (fr), Anglais (en), Néerlandais (nl).
    - Intégration de `wagtail-localize` et création des Locales en base de données.
    - Création d'un système de menus dynamiques et traduisibles (Snippets `Menu` et `MenuItem`).
    - Développement d'un sélecteur de langue interactif dans la barre de navigation.
    - Support de la traduction pour l'intégralité du catalogue (Modules, Catégories, Packs).

### Problèmes rencontrés et Résolutions :

1. **Défaut de style sur les pages d'authentification** :
    - **Description** : Les pages Login/Signup d'Allauth apparaissaient sans CSS (Tailwind manquant).
    - **Solution** : Surcharge des templates Allauth dans `app/templates/account/` pour qu'ils héritent de `base.html` et ajout de styles spécifiques pour les formulaires Django.

2. **Accumulation des préfixes de langue dans les URLs** :
    - **Description** : Le sélecteur de langue générait des URLs du type `/en/nl/` au lieu de remplacer le préfixe existant.
    - **Solution** : Correction du paramètre `next` dans le formulaire de changement de langue en utilisant un filtre `slice:"3:"` pour extraire proprement le chemin relatif.

3. **Erreur "no such table: core_menu"** :
    - **Description** : Erreur SQL lors de l'accès aux pages après ajout du modèle de menu.
    - **Solution** : Exécution des migrations (`makemigrations core` et `migrate`) après activation correcte de l'environnement virtuel.

4. **Conflit d'unicité sur les Slugs de Menus (UniqueConstraint E003)** :
    - **Description** : L'unicité stricte sur le champ `slug` empêchait de créer le même menu ("main-menu") dans plusieurs langues.
    - **Solution** : Modification du modèle `Menu` pour remplacer `unique=True` par un `unique_together = ("slug", "locale")` et ajout de la contrainte `UniqueConstraint` exigée par Wagtail 6+.

5. **Éléments de menu non dupliqués lors de la traduction** :
    - **Description** : Seul le titre du menu était envoyé à la traduction, les éléments (`InlinePanel`) restaient vides.
    - **Solution** : Ajout de `translatable_fields` sur les modèles `Menu` et `MenuItem`, et implémentation de `TranslatableMixin` sur le modèle enfant `MenuItem`.

6. **Erreur MultipleObjectsReturned sur les MenuItem** :
    - **Description** : Conflit de `translation_key` lors de la synchronisation des traductions suite à l'ajout tardif du mixin de traduction.
    - **Solution** : Nettoyage radical des tables `wagtail_localize` et réinitialisation des clés de traduction (`uuid`) via un script shell Python pour garantir l'intégrité des données.

7. **Erreur "DoesNotExist at /portal-management/localize/update/"** :
    - **Description** : Résidus de traductions corrompues dans les tables techniques de `wagtail-localize`.
    - **Solution** : Suppression manuelle des objets orphelins dans `Translation` et `TranslationSource` pour repartir sur une base saine.

8. **Routes catalog/ et content/ en 404** :
    - **Description** : Les routes n'acceptaient pas le préfixe de langue ou causaient des erreurs si elles étaient préfixées sans contenu correspondant.
    - **Solution** : Intégration correcte dans `i18n_patterns` avec `prefix_default_language=True` et ajout d'une vue par défaut pour l'application `content` pour éviter les `include` d'URLs vides.

### Outcome :
Le portail est désormais entièrement opérationnel en 3 langues. L'administrateur peut traduire chaque module, pack et menu directement depuis l'interface Wagtail avec une synchronisation parfaite des contenus.

---

## [04/04/2026] - Dynamisation Intégrale et Sécurisation des Données

### Avancement : Dynamisation de la Home Page
- **Description** : Suppression de tout le contenu codé en dur dans les templates pour permettre une gestion 100% via l'interface Wagtail et une traduction complète.
- **Implementation** :
    - **Section Hero** : Champs pour le titre, sous-titre, badge et boutons (textes et URLs).
    - **Barre de Statistiques** : Création d'un modèle `HomePageStat` (Orderable) pour gérer dynamiquement les chiffres clés.
    - **Terminal** : Création d'un modèle `HomePageTerminalLine` permettant de saisir les commandes et commentaires du terminal.
    - **Fonctionnalités** : Migration de la grille vers un modèle `HomePageFeature`.
    - **Marketplace & Packs** : Dynamisation des titres, sous-titres et messages d'absence de contenu.
    - **GitHub Bottom** : Intégration dynamique des textes de la section basse.

### Avancement : Optimisation GitHub API
- **Description** : Récupération automatique des étoiles et forks du dépôt SMARTOPS.
- **Implementation** :
    - Mise en place d'une fonction robuste avec gestion des exceptions (`RequestException`).
    - Implémentation d'un **cache de 6 heures** pour optimiser les performances et respecter les limites de l'API GitHub.
    - Formatage automatique des nombres (ex: `1.2k`) pour un rendu professionnel.

### Sécurité et Maintenance :
- **Système de Backup** : Création des commandes `python manage.py backup_portal` (export JSON complet) et `restore_portal` (restauration rapide).
- **Format d'Images** : Migration de tous les modèles de catalogue vers le format natif Wagtail (`ForeignKey` vers `wagtailimages.Image`) pour corriger les erreurs de rendu.

### Problèmes rencontrés et Résolutions :
1. **Erreur TypeError sur GitHub Stats** : Plantage du site si l'API GitHub ne répondait pas.
   - *Résolution* : Ajout de valeurs de fallback par défaut et d'un bloc try/except global.
2. **Perte de données lors de la migration des images** : SQLite ne permet pas de modifier une colonne ImageField en ForeignKey sans vider la table.
   - *Résolution* : Procédure de restauration via script pour réinitialiser le socle de base (superadmin, langues, menu principal).
3. **Segments de traduction manquants** : Wagtail Localize ne détectait pas les listes imbriquées.
   - *Résolution* : Ajout explicite de `translatable_fields` sur tous les modèles liés (Orderables).



---

## [18/04/2026] - Initialisation du socle Espace Client

### Avancement : Modélisation des Commandes et Licences
- **Description** : Création des modèles techniques nécessaires à la gestion des achats et des droits d'utilisation.
- **Implementation** :
    - **App 'payments'** : Modèles Order et OrderItem pour le suivi des transactions Stripe.
    - **App 'licensing'** : Modèle License avec génération d'UUID (license_key) et suivi des activations.
    - **Migrations** : Application des schémas en base de données SQLite.
- **Outcome** : Socle de données prêt pour l'implémentation du tableau de bord client.

---

## [18/04/2026] - Développement de l'Espace Client (Dashboard)

### Avancement : Interface du Tableau de Bord
- **Description** : Création d'une interface centrale pour permettre aux clients de consulter leurs achats et licences.
- **Implementation** :
    - **Vues** : Création de la vue 'dashboard' dans l'app accounts avec protection par @login_required.
    - **Templates** : Design du tableau de bord avec Tailwind CSS (sections Licences et Commandes).
    - **Navigation** : Intégration du lien vers le Dashboard dans la barre de navigation globale (base.html).
- **Outcome** : Les utilisateurs connectés disposent désormais d'un espace personnel dédié.

---

## [18/04/2026] - Automatisation des Ventes via Webhook Stripe

### Avancement : Implémentation du Webhook
- **Description** : Création d'un point de terminaison (Webhook) pour traiter les confirmations de paiement de Stripe et automatiser la livraison.
- **Implementation** :
    - **Vues** : Ajout de 'stripe_webhook' avec vérification de signature et traitement de l'événement 'checkout.session.completed'.
    - **Logique métier** : Création automatique d'une Order, d'un OrderItem et d'une License UUID lors de la réception du signal.
    - **Sécurité** : Utilisation de @csrf_exempt et STRIPE_WEBHOOK_SECRET pour sécuriser l'appel.
- **Outcome** : Le tunnel d'achat est désormais bouclé techniquement.

---

## [18/04/2026] - Finalisation du tunnel d'achat (Stripe CLI & Webhook)

### Avancement : Validation complète du circuit de paiement
- **Description** : Installation de Stripe CLI sur la machine locale et connexion au Webhook Django pour l'automatisation.
- **Implementation** :
    - **Outils** : Installation de 'stripe-cli' via apt. Authentification avec clé API.
    - **Configuration** : Tunnel 'stripe listen' pointant vers /fr/payments/stripe-webhook/.
    - **Environnement** : Mise à jour du fichier .env avec STRIPE_WEBHOOK_SECRET pour la signature.
- **Outcome** : Le système crée désormais automatiquement la commande et la licence en base de données dès que Stripe confirme le paiement.

---

## [18/04/2026] - Étape 7 : Intégration complète de Stripe et Espace Client

### Avancement : Tunnel d'achat fonctionnel et Dashboard Client
- **Description** : Mise en place du flux complet allant du catalogue de modules à la génération de licence après paiement sécurisé.
- **Implementation** :
    - **Modèles de données** : Création de 'Order' (Commandes) et 'License' (Licences UUID).
    - **Dashboard** : Interface utilisateur sous Tailwind CSS affichant les licences actives et l'historique d'achat.
    - **Paiement** : Intégration de Stripe Checkout (mode Test).
    - **Automatisation** : Système de Webhook pour la délivrance instantanée des produits.

### Problèmes rencontrés et Résolutions (Rapport Technique) :

1. **Absence de Stripe CLI sur l'environnement Linux** :
    - *Problème* : La commande 'stripe' n'était pas reconnue, empêchant les tests de Webhooks en local.
    - *Résolution* : Installation système via APT en suivant la documentation officielle : ajout de la clé GPG Stripe, configuration du dépôt debian-local, mise à jour d'apt et installation du binaire 'stripe'.
    - *Apprentissage* : Distinguer le SDK Python (pour le code) de la CLI système (pour les tests de tunnel).

2. **Échec des Webhooks dû à l'Internationalisation (i18n)** :
    - *Problème* : L'appel POST de Stripe sur '/payments/stripe-webhook/' était redirigé par Django vers '/fr/payments/stripe-webhook/' (Code 302), perdant ainsi le corps de la requête.
    - *Résolution* : Sortie de la route du Webhook du bloc 'i18n_patterns' dans 'urls.py' pour garantir une URL fixe et sans redirection.

3. **Incompatibilité d'accès aux données (AttributeError: get)** :
    - *Problème* : Tentative d'accès aux métadonnées Stripe via '.get()' sur l'objet 'Session'. Le SDK Stripe renvoie un 'StripeObject' qui ne se comporte pas comme un dictionnaire Python standard.
    - *Résolution* : Utilisation de l'accès direct par attribut 'session.metadata' couplé à l'accès par crochets '["user_id"]' après vérification de l'existence de l'attribut.
    - *Apprentissage* : Comprendre les spécificités des types d'objets retournés par les SDK tiers par rapport aux types natifs Python.

4. **Métadonnées manquantes (User:None, Module:None)** :
    - *Problème* : Le Webhook recevait bien l'événement mais les métadonnées étaient vides, empêchant la création de la licence.
    - *Cause* : Les métadonnées étaient placées uniquement dans 'payment_intent_data', alors que l'événement 'checkout.session.completed' porte sur l'objet Session lui-même.
    - *Résolution* : Placement des métadonnées à la racine de la 'Session' Stripe lors de sa création. Utilisation de 'client_reference_id' comme identifiant de secours ultra-fiable pour l'ID Utilisateur.

### Outcome Final :
Le tunnel est validé de bout en bout. Un test d'achat réel (mode test) a permis de confirmer :
1. La redirection vers Stripe.
2. Le traitement du Webhook par Django (Code 200).
3. La création automatique de la Commande #1 (250€) et de la Licence UUID dans la base de données.
4. L'affichage correct des données sur le Dashboard Client.

---

## [18/04/2026] - Unification de l'Administration (Wagtail & Django)

### Avancement : Centralisation de la gestion Marketplace
- **Description** : Intégration des modèles techniques (Commandes, Licences) dans l'interface Wagtail pour éviter de basculer entre deux panels d'administration.
- **Implementation** :
    - **Payments** : Enregistrement du modèle 'Order' comme Snippet Wagtail avec InlinePanel pour les 'OrderItems'.
    - **Licensing** : Enregistrement du modèle 'License' comme Snippet Wagtail.
    - **UI** : Configuration des Panels (FieldPanel, MultiFieldPanel) pour une édition ergonomique dans Wagtail.
- **Outcome** : L'administrateur gère désormais tout le business (Contenu, Catalogue, Ventes, Licences) depuis un point unique : /portal-management/.

---

## [18/04/2026] - Correction du Webhook et Stabilité Stripe

### Avancement : Fiabilisation du flux de paiement
- **Description** : Correction des bugs critiques empêchant la réception et le traitement des métadonnées Stripe.
- **Implementation** :
    - **Routage** : Déplacement de l'URL du Webhook hors de 'i18n_patterns' dans 'marketplace/urls.py' pour éviter les redirections 302 qui cassaient les requêtes POST.
    - **Stripe SDK** : Refonte de l'accès aux métadonnées dans 'payments/views.py' en utilisant l'accès par attribut direct (session.metadata["key"]) pour s'adapter aux objets StripeObject.
- **Outcome** : Le système identifie désormais correctement l'utilisateur et le module acheté, permettant l'enregistrement automatique.

---

## [18/04/2026] - Initialisation de l'Administration Custom (Backoffice)

### Avancement : Création de la tour de contrôle Admin
- **Description** : Mise en place d'une application d'administration dédiée, indépendante de Wagtail, pour le pilotage technique de la Marketplace.
- **Implementation** :
    - **App 'backoffice'** : Création de l'application et configuration dans 'settings.py'.
    - **UI** : Design d'une interface professionnelle avec barre latérale (Sidebar) et header via Tailwind CSS.
    - **Fonctionnalités** : Implémentation du Dashboard principal avec 4 indicateurs clés (Revenus, Licences, Ventes, Produits).
    - **Gestion Catalogue** : Création de vues custom pour lister les Modules et Packs avec calcul en temps réel du nombre de ventes et du CA généré par produit.
- **Outcome** : L'administrateur dispose d'un outil de pilotage métier sur-mesure et performant.

---

## [18/04/2026] - Système de Plugins Hot-Plug et API Marketplace

### Avancement : Prototype de Système de Plugins (POC)
- **Description** : Création d'un projet "SMARTOPS-POC" pour valider l'installation autonome de modules premium.
- **Implementation** :
    - **Cœur** : Utilisation de `Pluggy` pour le système de hooks (widgets dashboard, menus).
    - **Installation** : Automatisation via `pip install` de packages `.tar.gz` téléchargés dynamiquement.
    - **Désinstallation** : Système de nettoyage (logique en DB et physique via `pip uninstall`).
- **Outcome** : Validation technique de la boucle "Clé de licence -> API Marketplace -> Téléchargement -> Installation à chaud".

### Avancement : API de Distribution et Licensing (Marketplace)
- **Description** : Développement des points d'accès sécurisés pour le SMARTOPS CORE.
- **Implementation** :
    - **API Validate** : Endpoint `POST /api/licensing/validate/` retournant les métadonnées et l'URL de téléchargement.
    - **API Download** : Endpoint `GET /api/licensing/download/<uuid>/` servant le binaire du module après vérification de la licence.
- **Outcome** : La Marketplace est désormais capable de livrer ses modules de manière automatisée.

### Avancement : Suivi des Licences en Backoffice
- **Description** : Ajout d'une vue de monitoring des activations dans le tableau de bord Admin.
- **Implementation** :
    - **Vue** : Création de `license_list` avec métriques d'activation (utilisées/max).
    - **UI** : Template `licenses.html` intégré au design du backoffice.
    - **Navigation** : Interconnexion des barres latérales (Django Admin, Wagtail, Backoffice).
- **Outcome** : Visibilité totale sur les droits d'utilisation accordés aux clients.

### Avancement : UX Moderne et Internationalisation Totale
- **Description** : Refonte de la navigation utilisateur et traduction complète de l'interface client.
- **Implementation** :
    - **Navigation** : Menu déroulant utilisateur avec Alpine.js et transitions fluides.
    - **Internationalisation (i18n)** : Création et compilation des fichiers `.po` pour FR, EN, NL.
    - **Traduction** : Localisation des pages Dashboard, Profil, Email, Mot de passe et des statuts de commande.
- **Bug Fixes** :
    - **Doublons de Catégories** : Filtrage par `locale` active dans le catalogue pour éviter l'affichage de toutes les traductions.
    - **Routage Langue** : Correction du paramètre `next` dans le sélecteur de langue pour éviter la corruption d'URL sur les pages de compte.
- **Outcome** : Interface utilisateur professionnelle, robuste et 100% multilingue.

---

## [21/04/2026] - Sécurisation par Hardware Binding (UUID)

### Avancement : Implémentation du verrouillage par machine
- **Description** : Mise en place d'un système de sécurité liant une licence à une instance SMARTOPS unique (Hardware Binding).
- **Implementation** :
    - **Modèles** : Ajout du champ `installation_uuid` au modèle `License` pour mémoriser l'empreinte de la machine cliente.
    - **API de Validation** : Mise à jour de `ValidateLicenseAPI` pour exiger l'UUID de l'installation lors de la validation.
    - **Logique de Sécurité** : 
        - Première activation : L'UUID est enregistré sur la licence.
        - Activations suivantes : Le Portail vérifie la correspondance entre l'UUID envoyé et l'UUID stocké.
        - Refus (403 Forbidden) en cas de tentative d'activation sur une machine différente.
---

## [21/04/2026] - Extension du Monitoring et API de Télémétrie

### Avancement : Système de Synchronisation Globale
- **Description** : Mise en place d'un endpoint de synchronisation permettant de monitorer les installations (même sans licence) et de détecter les mises à jour.
- **Implementation** :
    - **Modèle Installation** : Passage du champ `user` en optionnel (`null=True`) pour autoriser le recensement des installations du "Cœur Open Source".
    - **Télémétrie** : Ajout du champ `core_version` pour suivre l'obsolescence du parc installé.
    - **API Sync** : Création de `SyncInstallationAPI` qui compare les versions locales envoyées par le client avec les dernières versions du catalogue.

### Problèmes rencontrés et Résolutions :

1. **Erreur de rendu sur les installations anonymes (VariableDoesNotExist)** :
    - **Description** : Le template du Backoffice plantait en essayant d'accéder à `inst.user.username` pour les installations non encore liées à un compte.
    - **Solution** : Ajout d'une condition `{% if inst.user %}` dans le template pour afficher "Installation Anonyme" le cas échéant.

2. **Échec de mise à jour du timestamp (L'optimisation paresseuse de Django)** :
    - **Description** : Le champ `last_sync` ne se mettait pas à jour si aucune donnée (nom, version) n'avait changé, rendant le monitoring imprécis.
    - **Solution** : Passage d'un `update_or_create` à un `get_or_create` suivi d'une affectation manuelle `timezone.now()` et d'un `save()` explicite pour forcer la mise à jour SQL.

3. **Inversion des ports (Erreur 404)** :
    - **Description** : Confusion lors des tests entre le port du Portail (8002) et celui du Client (8001).
    - **Solution** : Correction des URL de callback et création d'un fichier `credentials.txt` (hors Git) pour stabiliser la configuration.

- **Outcome** : Le Portail est désormais une véritable console de supervision capable de suivre l'état de santé technique de toutes les instances SMARTOPS déployées.

### Avancement : Libération de Licence et Gestion de Package
- **Description** : Finalisation du protocole de "Release" permettant aux clients de libérer leurs droits d'utilisation.
- **Implementation** :
    - **API Release** : Création de `ReleaseLicenseAPI` utilisant une vérification croisée stricte (License UUID + Installation UUID).
    - **Optimisation Package** : Rectification structurelle de l'archive ZIP du module de démo pour garantir la compatibilité "Hot-Plug" (structure à plat exigée par Django).
    - **Correction Bug 500** : Résolution d'un crash de génération d'URL de téléchargement dû au formatage des UUIDs.

- **Outcome Final** : La Marketplace SMARTOPS est 100% opérationnelle. Elle gère l'achat (Stripe), la livraison (Streaming API), le monitoring (UUID Binding) et la restitution des licences de manière totalement automatisée.

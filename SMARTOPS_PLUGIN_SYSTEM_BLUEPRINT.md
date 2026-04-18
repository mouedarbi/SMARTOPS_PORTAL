# SMARTOPS — Blueprint du Système de Plugins Premium

Ce document définit l'architecture et les étapes d'implémentation du système de modules extensibles pour **SMARTOPS CORE**. Il permet l'achat, l'installation automatique et l'activation de fonctionnalités "à chaud" via une clé de licence.

---

## 1. Architecture Technique
- **Moteur d'extension :** [Pluggy](https://pluggy.readthedocs.io/) (utilisé par Pytest).
- **Gestionnaire de paquets :** Pip (via `subprocess`).
- **Communication :** API REST (Requests) avec la Marketplace SMARTOPS.
- **Découverte :** Entry Points Python (`smartops.plugins`).

---

## 2. Étape 1 : Infrastructure Core (`smartops/plugins/`)

Créer un module transverse pour gérer la découverte des plugins.

### `hookspecs.py`
Définit les points d'entrée (interfaces) que les plugins peuvent implémenter.
- `register_dashboard_widgets()` : Retourne une liste de composants UI.
- `register_menu_items()` : Ajoute des entrées au menu principal.
- `process_core_data(data)` : Permet de modifier des flux de données internes.

### `registry.py`
Initialise le `PluginManager` de Pluggy et charge les `entry_points` du groupe `smartops.plugins`.

### `loader.py` (Crucial)
Fonction appelée dans `AppConfig.ready()`. 
**Règle d'or :** Elle doit filtrer les plugins physiquement installés par rapport à ceux qui sont marqués `is_active=True` en base de données pour éviter le chargement de modules non payés ou désactivés.

---

## 3. Étape 2 : L'App Django `module_management`

Cette application gère la persistance et l'interface utilisateur des licences.

### Modèle `Plugin`
- `slug` : Identifiant unique (ex: `smartops-iot-bundle`).
- `name` : Nom affichable.
- `license_key` : Hash de la clé.
- `is_active` : Booléen d'activation.

### `LicenseService`
Gère la communication avec l'API Marketplace :
1. Envoyer la clé à `https://marketplace.smartops.com/api/licensing/validate/`.
2. Récupérer le `download_url` et le `package_name`.
3. Lancer l'installateur.

---

## 4. Étape 3 : L'Installateur Automatique (`installer.py`)

Logique de manipulation de l'environnement virtuel.

1. **Téléchargement :** Utiliser un dossier temporaire (`tempfile`) pour récupérer le `.tar.gz`.
2. **Installation :** Exécuter `pip install <path_to_tar_gz>`.
3. **Migrations :** Lancer `call_command('migrate')` automatiquement après l'installation.
4. **Rechargement :**
   - *Dev :* Le `StatReloader` de Django redémarre tout seul.
   - *Prod :* Envoyer un signal `SIGHUP` au processus Gunicorn ou redémarrer le container Docker via une API de management.

---

## 5. Étape 4 : Intégration API Marketplace

La Marketplace doit exposer deux endpoints sécurisés :

1. **POST `/api/licensing/validate/`**
   - Entrée : `{ "license_key": "UUID" }`
   - Sortie : Métadonnées du module + `download_url` (URL temporaire ou signée).
2. **GET `/api/licensing/download/<uuid>/`**
   - Vérifie la validité de la licence.
   - Sert le fichier binaire `.tar.gz`.

---

## 6. Guide de création d'un Plugin (pour tiers)

Chaque plugin est un package Python standard avec un fichier `pyproject.toml` :

```toml
[project.entry-points."smartops.plugins"]
nom_unique = "mon_package.module:instance_classe_plugin"
```

Le code du plugin doit utiliser le marqueur `@hookimpl` pour répondre aux hooks du Core.

---

## 7. Sécurité et Bonnes Pratiques
- **Isolation :** Les plugins ne doivent jamais modifier directement les fichiers du Core.
- **Validation :** Toujours vérifier la compatibilité des versions (`min_core_version`) avant l'installation.
- **Sandboxing :** (Optionnel) Utiliser des environnements limités si les plugins proviennent de tiers non certifiés.
- **Cleanup :** La désinstallation doit supprimer l'entrée en DB, mais peut garder les données (tables) pour une réinstallation future (ou proposer un "Purge complète").

---

*Document généré le 18 Avril 2026 pour le projet SMARTOPS.*

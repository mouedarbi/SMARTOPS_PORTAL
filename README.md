# SMARTOPS Portal

Plateforme de distribution et de gestion de modules pour l'écosystème SMARTOPS. Permet aux utilisateurs de découvrir, acheter et gérer des licences de modules pour leur logiciel de gestion de maintenance.

## Prérequis

- Python 3.10+
- pip

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/mouedarbi/SMARTOPS_PORTAL.git
cd SMARTOPS_PORTAL
```

### 2. Créer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

Créez un fichier `.env` dans le dossier `app/` :

```env
DEBUG=True
SECRET_KEY=une-cle-secrete-quelconque
ALLOWED_HOSTS=localhost,127.0.0.1
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

> Les clés Stripe sont optionnelles pour tester l'interface. Le paiement ne sera pas fonctionnel sans clés valides.

### 4. Initialiser la base de données

```bash
cd app
python manage.py migrate
python manage.py createsuperuser
```

### 5. Lancer le serveur

```bash
python manage.py runserver
```

L'application est accessible sur **http://127.0.0.1:8000**

Le backoffice d'administration est accessible sur **http://127.0.0.1:8000/backoffice/**

## Tâche planifiée : anonymisation des comptes supprimés

Quand un client supprime son compte, celui-ci est seulement désactivé. Ses données personnelles sont anonymisées
plus tard par la commande `anonymize_deleted_accounts`, une fois écoulé le délai `ACCOUNT_ANONYMIZATION_DELAY_DAYS`
(30 jours par défaut, réglable dans `.env`). Les commandes et licences sont conservées.

```bash
cd app
python manage.py anonymize_deleted_accounts --dry-run   # liste les comptes concernés, sans rien modifier
python manage.py anonymize_deleted_accounts             # anonymise ; une ligne par compte dans logs/audit.log
```

La commande doit tourner une fois par jour sur le serveur, avec le même environnement que l'application (même
utilisateur système, même venv ; le fichier `.env` est lu par `settings.py`). Ligne de crontab installée sur le
serveur de production (`crontab -e` de l'utilisateur qui exécute le service, heure du serveur en UTC) :

```cron
0 3 * * * cd /root/smartops_portal/SMARTOPS_PORTAL/app && ../venv/bin/python manage.py anonymize_deleted_accounts >> logs/anonymize_deleted_accounts.log 2>&1
```

La commande est idempotente : la relancer ne modifie pas les comptes déjà anonymisés. Sans cette tâche, les comptes
supprimés ne seraient jamais anonymisés.

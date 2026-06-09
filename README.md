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

# SmartOps Portal

SmartOps Portal est une plateforme de gestion et de distribution de modules pour l'écosystème SmartOps. Cette version (Refonte 2.0) est bâtie sur Django 5.x pour offrir une performance optimale et une maintenance simplifiée.

## Prérequis

- **Système** : Linux (Ubuntu recommandé)
- **Langage** : Python 3.10+
- **Serveur Web** : Nginx
- **Gestionnaire de processus** : Gunicorn & Systemd

## Installation

### 1. Clonage du projet
```bash
git clone https://github.com/mouedarbi/SMARTOPS_PORTAL.git
cd SMARTOPS_PORTAL
```

### 2. Configuration de l'environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Variables d'environnement
Créez un fichier `.env` à la racine du projet :
```env
DEBUG=False
SECRET_KEY=votre_cle_secrete_django
ALLOWED_HOSTS=votre_domaine_ou_ip,localhost
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 4. Initialisation de la base de données
```bash
cd app
python manage.py migrate
python manage.py collectstatic --noinput
```

## Mise en production

### Configuration du service Gunicorn (Systemd)
Créez le fichier `/etc/systemd/system/smartops.service` :
```ini
[Unit]
Description=Gunicorn instance to serve SmartOps Portal
After=network.target

[Service]
User=<votre_utilisateur>
Group=www-data
WorkingDirectory=/opt/smartops/app
Environment="PATH=/opt/smartops/venv/bin"
ExecStart=/opt/smartops/venv/bin/gunicorn --workers 3 --bind unix:/opt/smartops/app/smartops.sock marketplace.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Configuration Nginx
```nginx
server {
    listen 80;
    server_name votre_ip_ou_domaine;

    location /static/ {
        alias /opt/smartops/app/static/;
    }

    location /media/ {
        alias /opt/smartops/app/media/;
    }

    location / {
        proxy_pass http://unix:/opt/smartops/app/smartops.sock;
        include proxy_params;
    }
}
```

## Maintenance
- **Redémarrer le service** : `systemctl restart smartops`
- **Consulter les logs** : `journalctl -u smartops -f`
- **Mise à jour du code** : 
  ```bash
  git pull
  source /opt/smartops/venv/bin/activate
  pip install -r requirements.txt
  python app/manage.py migrate
  systemctl restart smartops
  ```

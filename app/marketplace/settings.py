"""
Fichier : settings.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Configuration globale du projet Django Marketplace SMARTOPS.
              Gère les paramètres de sécurité, base de données et les middlewares.
"""

from pathlib import Path
import environ
import os

# Initialisation d'environ
env = environ.Env(
    DEBUG=(bool, False)
)

# BASE_DIR : Chemin racine du projet servant de base pour les autres chemins.
BASE_DIR = Path(__file__).resolve().parent.parent

# Lecture du fichier .env à la racine (un niveau au-dessus de 'app/')
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# SECRET_KEY : Clé secrète utilisée pour la cryptographie, fournie par le fichier .env
# (aucune valeur par défaut dans le code source).
SECRET_KEY = env('SECRET_KEY')

# DEBUG : désactivé par défaut ; le développement local l'active via DEBUG=True dans .env.
DEBUG = env.bool('DEBUG', default=False)

# Configuration Stripe
STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_API_VERSION = '2023-10-16'

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['opensmartops.org', 'www.opensmartops.org', '159.223.211.21', 'localhost', '127.0.0.1'])
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# CSRF_TRUSTED_ORIGINS : Obligatoire pour éviter les erreurs 403 en production (Login Allauth)
CSRF_TRUSTED_ORIGINS = ["https://opensmartops.org", "https://www.opensmartops.org"]

# --- SÉCURITÉ HTTPS ---
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
import sys
SECURE_SSL_REDIRECT = False if ('test' in sys.argv or 'test_coverage' in sys.argv) else True

# HSTS : Force les navigateurs à utiliser exclusivement HTTPS pendant 1 an
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Protection contre le clickjacking (refus d'intégration dans une iframe)
X_FRAME_OPTIONS = 'DENY'

# Protection contre le MIME sniffing (interdit au navigateur de deviner le type de contenu)
SECURE_CONTENT_TYPE_NOSNIFF = True

# Politique de référent : n'envoie l'URL complète qu'aux requêtes same-origin
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Limitation de débit allauth : détection de l'IP du client par l'adaptateur personnalisé
ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'
ACCOUNT_RATELIMIT_ENABLED = True

# Cache partagé entre les workers gunicorn : les compteurs de limitation de débit d'allauth
# (ex. 5 échecs de connexion par identifiant) sont communs à tous les processus.
# Table créée au déploiement par `python manage.py createcachetable`.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'portal_cache',
    }
}



# Applications installées

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Requis pour allauth
    'django.contrib.sitemaps',  # Requis pour le Sitemap XML SEO
    
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Applications SMARTOPS
    'core',
    'users',
    'catalog',
    'payments',
    'licensing',
    'downloads',
    'content',
    'backoffice',
]

# SITE_ID : Identifiant du site Django (requis pour allauth/sites)
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # Support de l'authentification par Django (ex: admin)
    'django.contrib.auth.backends.ModelBackend',
    # Support de l'authentification spécifique à allauth
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # Déplacé ici pour i18n avant Common/Csrf
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware allauth
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'marketplace.urls'

# Configuration spécifique à allauth (v65.15.0+)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
# Désactivation de la vérification email : permet l'inscription fluide de comptes de test fictifs
# pour les démonstrations et évite l'envoi de courriels réels si des adresses factices existent.
ACCOUNT_EMAIL_VERIFICATION = 'none'
# Aucun e-mail « mot de passe oublié » vers un compte supprimé (gelé pendant le délai de grâce).
ACCOUNT_FORMS = {'reset_password': 'users.forms.FrozenAccountAwareResetPasswordForm'}
# Type de compte (particulier ou professionnel) et coordonnées d'entreprise à l'inscription.
ACCOUNT_SIGNUP_FORM_CLASS = 'users.signup_forms.SignupForm'
# Nom d'URL plutôt que chemin : la redirection vers la connexion garde le préfixe de langue (/fr/, /en/, /nl/).
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Suppression de compte (RGPD art. 17) : le compte est d'abord désactivé, puis anonymisé par la
# commande planifiée `anonymize_deleted_accounts` une fois ce délai écoulé depuis la demande.
# 30 jours : délai de réponse d'un mois prévu par l'art. 12.3 RGPD.
ACCOUNT_ANONYMIZATION_DELAY_DAYS = env.int('ACCOUNT_ANONYMIZATION_DELAY_DAYS', default=30)

# Vendeur mentionné sur les factures des comptes professionnels. Valeurs FICTIVES par défaut :
# projet de fin d'études, sans numéro d'entreprise ni de TVA réels. La facture le signale tant que
# INVOICE_SELLER_FICTITIOUS vaut True.
INVOICE_SELLER = {
    'name': env('INVOICE_SELLER_NAME', default='SMARTOPS SRL'),
    'street': env('INVOICE_SELLER_STREET', default='Rue de la Démonstration 1'),
    'postal_code': env('INVOICE_SELLER_POSTAL_CODE', default='1000'),
    'city': env('INVOICE_SELLER_CITY', default='Bruxelles'),
    'country': 'BE',
    'company_number': env('INVOICE_SELLER_COMPANY_NUMBER', default='0987.654.394'),
    'vat_number': env('INVOICE_SELLER_VAT_NUMBER', default='BE0987654394'),
}
INVOICE_SELLER_FICTITIOUS = env.bool('INVOICE_SELLER_FICTITIOUS', default=True)
# Taux de TVA belge des produits numériques ; les prix affichés sont TVA comprise.
INVOICE_VAT_RATE = '21.00'

# E-mails transactionnels : en production, SMTP Gmail du compte opensmartops@gmail.com, réglé dans
# le .env (mot de passe d'application dans EMAIL_HOST_PASSWORD). Sans réglage, les e-mails sont
# écrits dans la console (développement) ; les tests utilisent toujours la boîte locale de Django.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
# Un serveur SMTP lent ne doit pas bloquer une page plus de quelques secondes.
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='SMARTOPS <opensmartops+info@gmail.com>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
# Destinataire des messages du formulaire de contact.
CONTACT_RECIPIENT = env('CONTACT_RECIPIENT', default='opensmartops+info@gmail.com')
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[SMARTOPS] '
# Pas d'e-mail « compte inconnu » quand on demande un nouveau mot de passe pour une adresse sans
# compte : sinon n'importe qui pourrait faire envoyer des e-mails à n'importe quelle adresse.
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'marketplace.wsgi.application'

# AUTH_USER_MODEL : Définit le modèle utilisé pour l'authentification.
AUTH_USER_MODEL = 'users.User'


# Base de données
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db_refonte.sqlite3"}')
}
if DATABASES['default'].get('ENGINE') == 'django.db.backends.mysql':
    DATABASES['default'].setdefault('OPTIONS', {})['charset'] = 'utf8mb4'
    DATABASES['default']['OPTIONS']['init_command'] = "SET names 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'"


# Validation des mots de passe
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalisation
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

LANGUAGES = [
    ('fr', 'French'),
    ('en', 'English'),
    ('nl', 'Dutch'),
]

# Fichiers statiques (CSS, JavaScript, images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Fichiers privés (APK de l'application mobile) : hors de MEDIA_ROOT, jamais servis directement.
# En production, nginx les envoie après contrôle (X-Accel-Redirect vers l'emplacement interne).
PRIVATE_MEDIA_ROOT = BASE_DIR / 'private'
PRIVATE_MEDIA_X_ACCEL_PREFIX = '/_private/'
USE_X_ACCEL_REDIRECT = env.bool('USE_X_ACCEL_REDIRECT', default=not DEBUG)
# Durée de validité d'un lien de téléchargement de l'APK (secondes).
MOBILE_APK_LINK_MAX_AGE = 600

# --- LOGGING ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_errors': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'formatter': 'verbose',
        },
        'file_audit': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_errors', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file_errors', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'audit': {
            'handlers': ['file_audit', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if "test" in sys.argv
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

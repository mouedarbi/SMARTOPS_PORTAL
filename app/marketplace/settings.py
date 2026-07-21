"""
Fichier : settings.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Configuration globale du projet Django Marketplace SMARTOPS (Version Sans Wagtail). 
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

# SECRET_KEY : Clé secrète utilisée pour la cryptographie.
SECRET_KEY = env('SECRET_KEY', default='django-insecure-m+!#i-4r-0_x_5_r_7_o_p_e_r_t_y_v_e_r_y_s_e_c_r_e_t')

# DEBUG : Mode débogage activé (True pour le développement, False en production).
DEBUG = env.bool('DEBUG', default=True)

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

# Fix Allauth Ratelimit / IP detection (Custom Adapter)
ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'
ACCOUNT_RATELIMIT_ENABLED = True



# Application definition

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Requis pour allauth
    
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Applications SMARTOPS (Refonte sans Wagtail)
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
ACCOUNT_EMAIL_VERIFICATION = 'optional'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

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


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_refonte.sqlite3',
    }
}


# Password validation
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


# Internationalization
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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

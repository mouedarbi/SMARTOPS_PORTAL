"""
Fichier : settings.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration globale du projet Django Marketplace SMARTOPS. 
              Gère les paramètres de sécurité, base de données et les middlewares.
"""

from pathlib import Path

# BASE_DIR : Chemin racine du projet servant de base pour les autres chemins.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY : Clé secrète utilisée pour la cryptographie (signatues, cookies, sessions).
SECRET_KEY = 'django-insecure-0$h%$l%@wi@b$@nxh&or&v3nvf^ed4u#&c@9sge4z795eb(!sl'

# DEBUG : Mode débogage activé (True pour le développement, False en production).
DEBUG = True

# ALLOWED_HOSTS : Liste des noms d'hôtes que le serveur peut servir.
ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
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
    
    # Applications SMARTOPS
    'core',
    'accounts',
    'catalog',
    'payments',
    'licensing',
    'downloads',
    'content',
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
    'django.contrib.sessions.middleware.SessionMiddleware',
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
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
# Suppression de ACCOUNT_SIGNUP_FIELDS car il est géré par défaut

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'marketplace.wsgi.application'

# AUTH_USER_MODEL : Définit le modèle utilisé pour l'authentification.
AUTH_USER_MODEL = 'accounts.User'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

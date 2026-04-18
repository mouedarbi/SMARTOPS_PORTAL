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
    
    # Wagtail
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.contrib.settings',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail.locales',
    'wagtail',
    
    'modelcluster',
    'taggit',

    # Wagtail Localize
    'wagtail_localize',
    
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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware', # Requis pour i18n
    # Middleware allauth
    'allauth.account.middleware.AccountMiddleware',
    # Middleware Wagtail
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
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

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ('fr', 'French'),
    ('en', 'English'),
    ('nl', 'Dutch'),
]

# Wagtail settings
WAGTAIL_SITE_NAME = "SMARTOPS Marketplace"
WAGTAILADMIN_BASE_URL = 'http://localhost:8001'
WAGTAIL_I18N_ENABLED = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

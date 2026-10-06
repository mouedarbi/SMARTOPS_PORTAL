"""
Fichier : wsgi.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Point d'entrée WSGI utilisé par gunicorn : expose ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

application = get_wsgi_application()

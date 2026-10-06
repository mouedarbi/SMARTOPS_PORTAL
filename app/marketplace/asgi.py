"""
Fichier : asgi.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Point d'entrée ASGI : expose l'application sous le nom ``application``.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

application = get_asgi_application()

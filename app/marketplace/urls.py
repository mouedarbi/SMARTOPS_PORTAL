"""
Configuration globale des URLs du Marketplace SMARTOPS.

Ce fichier définit les routes principales du serveur Django.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

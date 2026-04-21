"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.5
Description : Définition des routes API pour la validation et le téléchargement des licences.
"""

from django.urls import path
from .views import ValidateLicenseAPI, DownloadModulePackageAPI, SyncInstallationAPI

urlpatterns = [
    # API pour le cœur SMARTOPS
    path('validate/', ValidateLicenseAPI.as_view(), name='validate_license_api'),
    path('sync/', SyncInstallationAPI.as_view(), name='sync_installation_api'),
    path('download/<uuid:license_key>/', DownloadModulePackageAPI.as_view(), name='download_module_package'),
]

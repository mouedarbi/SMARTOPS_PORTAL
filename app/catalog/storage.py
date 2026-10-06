"""
Fichier : storage.py
Application : catalog
Description : Stockage privé des fichiers vendus (APK de l'application mobile), hors de MEDIA_ROOT :
              nginx ne les sert jamais directement, seulement après contrôle de la licence
              (X-Accel-Redirect vers un emplacement interne).
"""

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateMediaStorage(FileSystemStorage):
    """Fichiers rangés dans PRIVATE_MEDIA_ROOT, sans URL publique."""

    def __init__(self, **kwargs):
        kwargs.setdefault('base_url', None)
        super().__init__(**kwargs)

    @property
    def base_location(self):
        return self._value_or_setting(self._location, settings.PRIVATE_MEDIA_ROOT)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

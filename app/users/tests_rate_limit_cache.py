"""
Fichier : tests_rate_limit_cache.py
Projet : Marketplace SMARTOPS
Application : users
Description : Les compteurs de limitation de débit d'allauth sont stockés dans un cache partagé
              entre les workers (base de données).
"""

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase


class SharedRateLimitCacheTests(TestCase):

    def test_cache_is_shared_between_workers(self):
        self.assertEqual(settings.CACHES['default']['BACKEND'], 'django.core.cache.backends.db.DatabaseCache')
        cache.set('portal-cache-check', 'ok', 30)
        self.assertEqual(cache.get('portal-cache-check'), 'ok')

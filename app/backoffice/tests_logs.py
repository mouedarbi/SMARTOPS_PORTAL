"""
Fichier : tests_logs.py
Projet : Marketplace SMARTOPS
Application : backoffice
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Visualiseur du journal applicatif (audit.log) : entrées les plus récentes en premier.
"""

import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

User = get_user_model()


class AuditLogViewerOrderTests(TestCase):

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        (Path(self.tmp.name) / 'logs').mkdir()
        self.log_file = Path(self.tmp.name) / 'logs' / 'audit.log'
        admin = User.objects.create_superuser('root_logs', 'root_logs@example.org', 'x')
        self.client.force_login(admin)

    def log_content(self):
        with override_settings(BASE_DIR=Path(self.tmp.name)):
            return self.client.get(reverse('backoffice:logs_view')).context['log_content']

    def test_most_recent_entry_first(self):
        self.log_file.write_text(
            "[2026-09-27 10:00:00,000] INFO audit PREMIER\n"
            "[2026-09-27 11:00:00,000] ERROR licensing.views DEUXIEME\n"
            "Traceback (most recent call last):\n"
            "  File \"x.py\", line 1\n"
            "[2026-09-27 12:00:00,000] INFO audit TROISIEME\n",
            encoding='utf-8',
        )
        content = self.log_content()
        self.assertLess(content.index('TROISIEME'), content.index('DEUXIEME'))
        self.assertLess(content.index('DEUXIEME'), content.index('PREMIER'))
        # la trace reste attachée à son entrée, dans l'ordre
        self.assertIn('DEUXIEME\nTraceback (most recent call last):\n  File "x.py", line 1\n', content)

    def test_only_the_last_200_entries_are_shown(self):
        self.log_file.write_text(''.join(f"[2026-09-27 10:00:00,000] INFO audit EVT{i:03d}\n" for i in range(250)),
                                 encoding='utf-8')
        content = self.log_content()
        self.assertTrue(content.startswith('[2026-09-27 10:00:00,000] INFO audit EVT249'))
        self.assertIn('EVT050', content)
        self.assertNotIn('EVT049', content)

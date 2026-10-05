from django.conf import settings
from django.db import migrations


def name_site(apps, schema_editor):
    """Nom du site repris dans les e-mails de compte (« Bonjour, c'est SMARTOPS ! »)."""
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(pk=settings.SITE_ID,
                                  defaults={'domain': 'www.opensmartops.org', 'name': 'SMARTOPS'})


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_purge_anonymized_email_addresses'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(name_site, migrations.RunPython.noop),
    ]

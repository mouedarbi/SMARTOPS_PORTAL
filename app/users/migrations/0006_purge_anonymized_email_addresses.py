from django.db import migrations

ANONYMIZED_EMAIL_DOMAIN = '@supprime.invalid'


def purge(apps, schema_editor):
    """Comptes déjà anonymisés : supprime la copie de l'adresse e-mail gardée par allauth."""
    User = apps.get_model('users', 'User')
    anonymized = User.objects.filter(is_deleted=True, email__endswith=ANONYMIZED_EMAIL_DOMAIN).values('pk')
    apps.get_model('account', 'EmailAddress').objects.filter(user__in=anonymized).delete()
    apps.get_model('socialaccount', 'SocialAccount').objects.filter(user__in=anonymized).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_account_type_billing_profile'),
        ('account', '0009_emailaddress_unique_primary_email'),
        ('socialaccount', '0006_alter_socialaccount_extra_data'),
    ]

    operations = [
        migrations.RunPython(purge, migrations.RunPython.noop),
    ]

from django.db import migrations

UNCATEGORIZED_SLUG = 'non-classe'
NAMES = {'fr': 'Non classé', 'en': 'Uncategorized', 'nl': 'Niet ingedeeld'}
SLUGS = {'fr': UNCATEGORIZED_SLUG, 'en': 'uncategorized', 'nl': 'niet-ingedeeld'}


def create_uncategorized(apps, schema_editor):
    """Crée la catégorie « Non classé » et y range les modules qui n'ont pas de catégorie."""
    Category = apps.get_model('catalog', 'Category')
    Module = apps.get_model('catalog', 'Module')
    category = Category.objects.filter(slug_fr=UNCATEGORIZED_SLUG).first()
    if category is None:
        fields = {'name': NAMES['fr'], 'slug': UNCATEGORIZED_SLUG, 'icon': '📦'}
        for lang in ('fr', 'en', 'nl'):
            fields[f'name_{lang}'] = NAMES[lang]
            fields[f'slug_{lang}'] = SLUGS[lang]
        category = Category.objects.create(**fields)
    Module.objects.filter(category__isnull=True).update(category=category)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_module_category_set_default'),
    ]

    operations = [
        migrations.RunPython(create_uncategorized, migrations.RunPython.noop),
    ]

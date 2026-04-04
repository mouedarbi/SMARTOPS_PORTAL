"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 1.4
Description : Modèles pour le catalogue de modules (plugins) et packs promotionnels. 
              Utilise les images Wagtail pour une meilleure intégration CMS.
"""

from django.db import models
from django.forms import CheckboxSelectMultiple
from django.utils.text import slugify
from django.utils import timezone
from wagtail.snippets.models import register_snippet
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.models import Orderable, TranslatableMixin
from wagtail_localize.fields import TranslatableField
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel

@register_snippet
class Category(TranslatableMixin, models.Model):
    """
    Catégories de modules (ex: IoT, Mobile, Analytics).
    """
    locale = models.ForeignKey(
        'wagtailcore.Locale',
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True, blank=True
    )
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(help_text="Slug unique pour la catégorie")
    icon = models.CharField(max_length=50, help_text="Emoji ou nom d'icône Lucide", default="📦")

    translatable_fields = [
        TranslatableField("name"),
    ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta(TranslatableMixin.Meta):
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        unique_together = ("slug", "locale")
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_catalog_category",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.locale})"

@register_snippet
class CoreVersion(models.Model):
    """
    Versions du cœur de l'application de maintenance (Core).
    """
    version = models.CharField(max_length=20, unique=True, verbose_name="Version du Cœur")
    release_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Version supportée")

    class Meta:
        verbose_name = "Version Core"
        verbose_name_plural = "Versions Core"
        ordering = ['-version']

    def __str__(self):
        return f"Core v{self.version}"

class Module(TranslatableMixin, ClusterableModel):
    """
    Modèle principal pour un module (Plugin).
    """
    locale = models.ForeignKey(
        'wagtailcore.Locale',
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True, blank=True
    )
    name = models.CharField(max_length=255, verbose_name="Nom du module")
    slug = models.SlugField(help_text="Slug pour l'URL")
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="modules",
        verbose_name="Catégorie"
    )
    
    short_description = models.TextField(
        max_length=500, 
        verbose_name="Description courte",
        help_text="Affichée sur les cartes du catalogue."
    )
    description = RichTextField(verbose_name="Description complète")
    
    # Utilisation de Wagtail Image au lieu de Django ImageField
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Image de mise en avant"
    )
    
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Prix (Paiement unique)"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    translatable_fields = [
        TranslatableField("name"),
        TranslatableField("short_description"),
        TranslatableField("description"),
        TranslatableField("screenshots"),
        TranslatableField("versions"),
    ]

    # Panels pour l'administration Wagtail
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('slug'),
            FieldPanel('category'),
            FieldPanel('is_active'),
        ], heading="Informations de base"),
        MultiFieldPanel([
            FieldPanel('price'),
            FieldPanel('featured_image'),
        ], heading="Vente"),
        FieldPanel('short_description'),
        FieldPanel('description'),
        InlinePanel('screenshots', label="Captures d'écran"),
        InlinePanel('versions', label="Versions du module"),
    ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta(TranslatableMixin.Meta):
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        unique_together = ("slug", "locale")
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_catalog_module",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.locale})"

class ModuleScreenshot(TranslatableMixin, models.Model):
    """
    Captures d'écran pour la galerie du module.
    """
    locale = models.ForeignKey(
        'wagtailcore.Locale',
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True, blank=True
    )
    module = ParentalKey(Module, on_delete=models.CASCADE, related_name='screenshots')
    
    # Image Wagtail
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name="Capture d'écran"
    )
    
    caption = models.CharField(max_length=255, blank=True, verbose_name="Légende")

    translatable_fields = [
        TranslatableField("caption"),
    ]

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]

    class Meta(TranslatableMixin.Meta):
        unique_together = None
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_catalog_screenshot",
            )
        ]

class ModuleVersion(TranslatableMixin, models.Model):
    """
    Versions spécifiques d'un module avec fichier et compatibilité.
    """
    locale = models.ForeignKey(
        'wagtailcore.Locale',
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True, blank=True
    )
    module = ParentalKey(Module, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20, verbose_name="N° de version (ex: 1.2.0)")
    release_date = models.DateField(verbose_name="Date de sortie")
    
    min_core_version = models.ForeignKey(
        CoreVersion, 
        on_delete=models.PROTECT, 
        verbose_name="Version Core minimale requise"
    )
    
    changelog = models.TextField(blank=True, verbose_name="Notes de version")
    
    file = models.FileField(
        upload_to='modules/packages/', 
        verbose_name="Package (.zip / .tar.gz)"
    )

    translatable_fields = [
        TranslatableField("changelog"),
    ]

    panels = [
        FieldPanel('version_number'),
        FieldPanel('release_date'),
        FieldPanel('min_core_version'),
        FieldPanel('file'),
        FieldPanel('changelog'),
    ]

    class Meta(TranslatableMixin.Meta):
        verbose_name = "Version de module"
        verbose_name_plural = "Versions de modules"
        unique_together = None
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_catalog_version",
            )
        ]

    def __str__(self):
        return f"{self.module.name} v{self.version_number}"

@register_snippet
class ModuleBundle(TranslatableMixin, ClusterableModel):
    """
    Packs de modules permettant des promotions groupées.
    """
    locale = models.ForeignKey(
        'wagtailcore.Locale',
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True, blank=True
    )
    DISCOUNT_MODES = [
        ('PERCENTAGE', 'Remise en pourcentage sur le total'),
        ('FIXED', 'Prix fixe pour le pack (Ristourne manuelle)'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nom du pack")
    slug = models.SlugField(help_text="Slug pour l'URL")
    
    modules = ParentalManyToManyField(
        'catalog.Module', 
        related_name='bundles',
        verbose_name="Modules inclus"
    )
    
    short_description = models.TextField(max_length=500, verbose_name="Description courte")
    description = RichTextField(verbose_name="Description complète")
    
    # Image Wagtail
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Image du pack"
    )

    discount_mode = models.CharField(
        max_length=20, 
        choices=DISCOUNT_MODES, 
        default='PERCENTAGE',
        verbose_name="Mode de remise"
    )
    
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Valeur (Remise % ou Prix Fixe)",
        help_text="Si mode Pourcentage: entrez 20 pour -20%. Si mode Prix Fixe: entrez le prix final."
    )

    start_date = models.DateTimeField(
        null=True, blank=True, 
        verbose_name="Date de début",
        help_text="Laisser vide pour une activation immédiate."
    )
    end_date = models.DateTimeField(
        null=True, blank=True, 
        verbose_name="Date de fin",
        help_text="Laisser vide pour une durée illimitée."
    )

    is_active = models.BooleanField(default=True, verbose_name="Actif")

    translatable_fields = [
        TranslatableField("name"),
        TranslatableField("short_description"),
        TranslatableField("description"),
    ]

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('slug'),
            FieldPanel('is_active'),
        ], heading="Informations générales"),
        FieldPanel('modules', widget=CheckboxSelectMultiple),
        MultiFieldPanel([
            FieldPanel('discount_mode'),
            FieldPanel('discount_value'),
        ], heading="Configuration du prix"),
        MultiFieldPanel([
            FieldPanel('start_date'),
            FieldPanel('end_date'),
        ], heading="Période de validité"),
        FieldPanel('featured_image'),
        FieldPanel('short_description'),
        FieldPanel('description'),
    ]

    @property
    def total_original_price(self):
        """Calcule la somme des prix individuels des modules."""
        return sum(module.price for module in self.modules.all())

    @property
    def final_price(self):
        """Calcule le prix final du pack selon le mode choisi."""
        if self.discount_mode == 'PERCENTAGE':
            total = self.total_original_price
            discount = (self.discount_value / 100) * total
            return total - discount
        return self.discount_value

    @property
    def is_currently_valid(self):
        """Vérifie si le pack est actuellement valide temporellement."""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta(TranslatableMixin.Meta):
        verbose_name = "Pack de modules"
        verbose_name_plural = "Packs de modules"
        unique_together = ("slug", "locale")
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_catalog_bundle",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.locale})"

# Enregistrement du module comme snippet pour Wagtail
register_snippet(Module)

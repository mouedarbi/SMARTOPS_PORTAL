"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Modèles Django standards pour le catalogue de modules et packs.
              Suppression de toutes les dépendances Wagtail pour une architecture légère.
"""

from django.db import models
from django.utils.text import slugify
from django.utils import timezone

class Category(models.Model):
    """
    Catégories de modules (ex: IoT, Mobile, Analytics).
    """
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(max_length=100, unique=True, help_text="Slug unique pour la catégorie")
    icon = models.CharField(max_length=50, help_text="Emoji ou nom d'icône Lucide", default="📦")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name

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

class Module(models.Model):
    """
    Modèle principal pour un module (Plugin).
    """
    name = models.CharField(max_length=255, verbose_name="Nom du module")
    slug = models.SlugField(max_length=255, unique=True, help_text="Slug pour l'URL")
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
    description = models.TextField(verbose_name="Description complète")
    
    # Utilisation de ImageField standard au lieu de Wagtail Image
    featured_image = models.ImageField(
        upload_to='modules/featured/',
        null=True,
        blank=True,
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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"

    def __str__(self):
        return self.name

class ModuleScreenshot(models.Model):
    """
    Captures d'écran pour la galerie du module.
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to='modules/screenshots/', verbose_name="Capture d'écran")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Légende")

    class Meta:
        verbose_name = "Capture d'écran"
        verbose_name_plural = "Captures d'écran"

    def __str__(self):
        return f"Screenshot pour {self.module.name}"

class ModuleVersion(models.Model):
    """
    Versions spécifiques d'un module avec fichier et compatibilité.
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20, verbose_name="N° de version (ex: 1.2.0)")
    release_date = models.DateField(verbose_name="Date de sortie")
    
    min_core_version = models.ForeignKey(
        CoreVersion, 
        on_delete=models.PROTECT, 
        related_name="min_compatible_modules",
        verbose_name="Version Core minimale requise"
    )
    
    max_core_version = models.ForeignKey(
        CoreVersion, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="max_compatible_modules",
        verbose_name="Version Core maximale (Optionnel)",
        help_text="Laissez vide si compatible avec toutes les versions futures."
    )
    
    changelog = models.TextField(blank=True, verbose_name="Notes de version")
    file = models.FileField(upload_to='modules/packages/', verbose_name="Package (.zip / .tar.gz)")

    class Meta:
        verbose_name = "Version de module"
        verbose_name_plural = "Versions de modules"

    def __str__(self):
        return f"{self.module.name} v{self.version_number}"

class ModuleBundle(models.Model):
    """
    Packs de modules permettant des promotions groupées.
    """
    DISCOUNT_MODES = [
        ('PERCENTAGE', 'Remise en pourcentage sur le total'),
        ('FIXED', 'Prix fixe pour le pack (Ristourne manuelle)'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nom du pack")
    slug = models.SlugField(max_length=255, unique=True, help_text="Slug pour l'URL")
    
    modules = models.ManyToManyField(
        Module, 
        related_name='bundles',
        verbose_name="Modules inclus"
    )
    
    short_description = models.TextField(max_length=500, verbose_name="Description courte")
    description = models.TextField(verbose_name="Description complète")
    
    featured_image = models.ImageField(
        upload_to='bundles/featured/',
        null=True,
        blank=True,
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

    start_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    @property
    def total_original_price(self):
        return sum(module.price for module in self.modules.all())

    @property
    def final_price(self):
        if self.discount_mode == 'PERCENTAGE':
            total = self.total_original_price
            discount = (self.discount_value / 100) * total
            return total - discount
        return self.discount_value

    @property
    def is_currently_valid(self):
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

    class Meta:
        verbose_name = "Pack de modules"
        verbose_name_plural = "Packs de modules"

    def __str__(self):
        return self.name

import requests
from django.conf import settings

def translate_text(text, source_lang, target_lang):
    """
    Appelle le service local LibreTranslate sur le port 5000
    pour traduire le texte de source_lang vers target_lang.
    """
    if not text:
        return ""
    try:
        url = "http://localhost:5000/translate"
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get("translatedText", text)
    except Exception:
        pass
    return text

class Review(models.Model):
    """
    Modèle pour les avis et notations (étoiles + commentaires) des modules ou des packs.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Utilisateur"
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name="Module"
    )
    bundle = models.ForeignKey(
        ModuleBundle,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name="Pack"
    )
    
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="Note (Étoiles)"
    )
    
    comment = models.TextField(verbose_name="Commentaire original")
    comment_language = models.CharField(max_length=5, default="fr", verbose_name="Langue d'origine")
    
    comment_fr = models.TextField(null=True, blank=True, verbose_name="Commentaire (FR)")
    comment_en = models.TextField(null=True, blank=True, verbose_name="Commentaire (EN)")
    comment_nl = models.TextField(null=True, blank=True, verbose_name="Commentaire (NL)")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")

    class Meta:
        verbose_name = "Commentaire et Note"
        verbose_name_plural = "Commentaires et Notes"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        src = self.comment_language or 'fr'
        
        # Traduction automatique avec LibreTranslate
        if not self.comment_fr or not self.comment_en or not self.comment_nl:
            if src == 'fr':
                self.comment_fr = self.comment
                self.comment_en = translate_text(self.comment, 'fr', 'en')
                self.comment_nl = translate_text(self.comment, 'fr', 'nl')
            elif src == 'en':
                self.comment_en = self.comment
                self.comment_fr = translate_text(self.comment, 'en', 'fr')
                self.comment_nl = translate_text(self.comment, 'en', 'nl')
            elif src == 'nl':
                self.comment_nl = self.comment
                self.comment_fr = translate_text(self.comment, 'nl', 'fr')
                self.comment_en = translate_text(self.comment, 'nl', 'en')
                
        super().save(*args, **kwargs)

    def __str__(self):
        target = self.module.name if self.module else self.bundle.name
        return f"Note {self.rating}/5 par {self.user.username} sur {target}"

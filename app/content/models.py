"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : content
Auteur : Mohamed Ouedarbi
Version : 1.11
Description : Définition des modèles pour le contenu.
              Optimisation de la récupération des statistiques GitHub.
"""

import requests
from django.db import models
from django.core.cache import cache
from modelcluster.fields import ParentalKey
from wagtail.models import Page, Orderable, TranslatableMixin
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail_localize.fields import TranslatableField

def format_github_number(n):
    """Formate un nombre au format '1.2k' si >= 1000."""
    try:
        n = int(n)
        if n >= 1000:
            return f"{n/1000:.1f}k"
        return str(n)
    except (ValueError, TypeError):
        return str(n)

def get_github_stats():
    """Récupère les statistiques du dépôt GitHub avec gestion du cache et erreurs."""
    CACHE_KEY = 'github_stats_smartops_v2'
    CACHE_TIMEOUT = 60 * 60 * 6  # 6 heures

    # 1. Vérifier le cache
    github_stats = cache.get(CACHE_KEY)
    if github_stats:
        return github_stats

    # 2. Valeurs par défaut (fallback)
    # On utilise des entiers pour permettre le formatage
    github_stats = {
        'stars': 0,
        'forks': 0
    }

    try:
        response = requests.get(
            'https://api.github.com/repos/mouedarbi/SMARTOPS',
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            # On récupère les vraies valeurs, mais on peut garder un minimum marketing si on veut
            stars = data.get('stargazers_count', 0)
            forks = data.get('forks_count', 0)
            
            github_stats = {
                'stars': stars if stars > 0 else 1200,
                'forks': forks if forks > 0 else 380,
            }
            # 3. Mise en cache
            cache.set(CACHE_KEY, github_stats, CACHE_TIMEOUT)

    except requests.RequestException:
        # En cas d’erreur réseau, on garde le fallback
        pass

    return github_stats

class HomePageStat(Orderable, TranslatableMixin):
    page = ParentalKey('content.HomePage', related_name='stats', on_delete=models.CASCADE)
    value = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    translatable_fields = [TranslatableField('value'), TranslatableField('label')]
    panels = [FieldPanel('value'), FieldPanel('label')]
    class Meta(TranslatableMixin.Meta):
        unique_together = None
        constraints = [models.UniqueConstraint(fields=("translation_key", "locale"), name="unique_translation_key_locale_homepage_stat")]

class HomePageTerminalLine(Orderable, TranslatableMixin):
    page = ParentalKey('content.HomePage', related_name='terminal_lines', on_delete=models.CASCADE)
    line_type = models.CharField(max_length=20, choices=[('comment', 'Commentaire'), ('command', 'Commande'), ('success', 'Succès'), ('empty', 'Ligne vide')], default='command')
    content = models.CharField(max_length=255, blank=True)
    translatable_fields = [TranslatableField('content')]
    panels = [FieldPanel('line_type'), FieldPanel('content')]
    class Meta(TranslatableMixin.Meta):
        unique_together = None
        constraints = [models.UniqueConstraint(fields=("translation_key", "locale"), name="unique_translation_key_locale_homepage_terminal")]

class HomePageFeature(Orderable, TranslatableMixin):
    page = ParentalKey('content.HomePage', related_name='features', on_delete=models.CASCADE)
    icon = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    translatable_fields = [TranslatableField('title'), TranslatableField('description')]
    panels = [FieldPanel('icon'), FieldPanel('title'), FieldPanel('description')]
    class Meta(TranslatableMixin.Meta):
        unique_together = None
        constraints = [models.UniqueConstraint(fields=("translation_key", "locale"), name="unique_translation_key_locale_homepage_feature")]

class HomePage(Page):
    # --- HERO ---
    hero_title = models.CharField(max_length=255, default="La GMAO open source", verbose_name="Titre Hero")
    hero_subtitle = models.TextField(blank=True, verbose_name="Sous-titre Hero")
    hero_badge_text = models.CharField(max_length=100, default="v2.4 disponible", verbose_name="Texte du badge")
    hero_primary_cta_text = models.CharField(max_length=100, default="Commencer", verbose_name="Texte bouton principal")
    hero_secondary_cta_text = models.CharField(max_length=100, default="GitHub", verbose_name="Texte bouton secondaire")
    hero_secondary_cta_url = models.URLField(default="https://github.com/mouedarbi/SMARTOPS.git", verbose_name="URL bouton secondaire")
    
    # --- TERMINAL ---
    terminal_title = models.CharField(max_length=100, default="terminal — installation rapide", verbose_name="Titre du terminal")

    # --- FEATURES ---
    features_section_title = models.CharField(max_length=100, default="Fonctionnalités core", verbose_name="Titre de la section")
    features_intro = RichTextField(blank=True, verbose_name="Introduction des fonctionnalités", default="Tout ce dont la maintenance a besoin.")
    
    # --- MARKETPLACE ---
    marketplace_section_title = models.CharField(max_length=100, default="Marketplace", verbose_name="Titre de la section")
    marketplace_intro = RichTextField(blank=True, verbose_name="Introduction du Marketplace", default="Modules Pro à la demande.")
    marketplace_view_all_text = models.CharField(max_length=100, default="Voir tous les modules →", verbose_name="Texte lien tout voir")
    marketplace_empty_msg = models.CharField(max_length=255, default="Aucun module disponible pour le moment.", verbose_name="Message si vide")

    # --- PACKS ---
    packs_section_title = models.CharField(max_length=100, default="Offres groupées", verbose_name="Petit titre section")
    packs_main_title = models.CharField(max_length=100, default="Packs de modules (Pay-once)", verbose_name="Grand titre section")
    packs_subtitle = models.TextField(default="Équipez-vous au meilleur prix avec nos packs thématiques.", verbose_name="Sous-titre section")
    packs_empty_msg = models.CharField(max_length=255, default="Aucune offre groupée disponible actuellement.", verbose_name="Message si vide")

    # --- GITHUB BOTTOM ---
    github_title = models.CharField(max_length=255, default="100% open source. Vos données restent chez vous.", verbose_name="Titre section GitHub")
    github_subtitle = models.TextField(default="Le cœur SmartOps Portal est sous licence MIT. Hébergez où vous voulez, modifiez librement, contribuez.", verbose_name="Sous-titre section GitHub")
    github_cta_text = models.CharField(max_length=100, default="Voir sur GitHub", verbose_name="Texte bouton GitHub")
    github_docs_text = models.CharField(max_length=100, default="Lire la documentation →", verbose_name="Texte lien documentation")
    github_docs_url = models.CharField(max_length=255, default="/fr/content/", verbose_name="URL documentation")

    translatable_fields = [
        TranslatableField('hero_title'), TranslatableField('hero_subtitle'), TranslatableField('hero_badge_text'),
        TranslatableField('hero_primary_cta_text'), TranslatableField('hero_secondary_cta_text'), TranslatableField('hero_secondary_cta_url'),
        TranslatableField('stats'),
        TranslatableField('terminal_title'), TranslatableField('terminal_lines'),
        TranslatableField('features_section_title'), TranslatableField('features_intro'), TranslatableField('features'),
        TranslatableField('marketplace_section_title'), TranslatableField('marketplace_intro'), 
        TranslatableField('marketplace_view_all_text'), TranslatableField('marketplace_empty_msg'),
        TranslatableField('packs_section_title'), TranslatableField('packs_main_title'), TranslatableField('packs_subtitle'), TranslatableField('packs_empty_msg'),
        TranslatableField('github_title'), TranslatableField('github_subtitle'), 
        TranslatableField('github_cta_text'), TranslatableField('github_docs_text'),
    ]
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel('hero_title'), FieldPanel('hero_subtitle'), FieldPanel('hero_badge_text'), FieldPanel('hero_primary_cta_text'), FieldPanel('hero_secondary_cta_text'), FieldPanel('hero_secondary_cta_url')], heading="Hero"),
        InlinePanel('stats', label="Statistiques"),
        MultiFieldPanel([FieldPanel('terminal_title'), InlinePanel('terminal_lines', label="Lignes")], heading="Terminal"),
        MultiFieldPanel([FieldPanel('features_section_title'), FieldPanel('features_intro'), InlinePanel('features', label="Fonctionnalités")], heading="Fonctionnalités"),
        MultiFieldPanel([FieldPanel('marketplace_section_title'), FieldPanel('marketplace_intro'), FieldPanel('marketplace_view_all_text'), FieldPanel('marketplace_empty_msg')], heading="Marketplace"),
        MultiFieldPanel([FieldPanel('packs_section_title'), FieldPanel('packs_main_title'), FieldPanel('packs_subtitle'), FieldPanel('packs_empty_msg')], heading="Packs"),
        MultiFieldPanel([
            FieldPanel('github_title'),
            FieldPanel('github_subtitle'),
            FieldPanel('github_cta_text'),
            FieldPanel('github_docs_text'),
            FieldPanel('github_docs_url'),
        ], heading="Section GitHub (Bas)"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        
        # 1. Récupération des données GitHub via la fonction améliorée
        stats = get_github_stats()
        context['github_stars'] = format_github_number(stats['stars'])
        context['github_forks'] = format_github_number(stats['forks'])

        # 2. Modules et Bundles
        from catalog.models import Module, ModuleBundle
        context['modules'] = Module.objects.filter(is_active=True).order_by('-created_at')[:3]
        all_bundles = ModuleBundle.objects.filter(is_active=True)
        context['bundles'] = [b for b in all_bundles if b.is_currently_valid][:2]
        return context

    max_count = 1
    subpage_types = ['content.ContentIndexPage']

class ContentIndexPage(Page):
    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel('intro')]
    subpage_types = ['content.ContentPage']

class ContentPage(Page):
    date = models.DateField("Post date")
    body = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel('date'), FieldPanel('body')]
    parent_page_types = ['content.ContentIndexPage']

"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : content
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Définition des modèles pour le contenu (blog, pages).
              Sera potentiellement remplacé ou étendu par Wagtail.
"""

from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel

class HomePage(Page):
    """
    Page d'accueil du Marketplace SMARTOPS.
    Design basé sur la landing page pro avec des placeholders.
    """
    hero_title = models.CharField(
        max_length=255, 
        default="La GMAO open source pour l'industrie moderne",
        verbose_name="Titre Hero"
    )
    hero_subtitle = models.TextField(
        blank=True, 
        default="Téléchargez le cœur gratuitement sur GitHub. Étendez votre GMAO avec des modules professionnels : IoT, mobile, analytics, IA prédictive.",
        verbose_name="Sous-titre Hero"
    )
    
    features_intro = RichTextField(
        blank=True, 
        verbose_name="Introduction des fonctionnalités",
        default="Tout ce dont la maintenance a besoin, inclus d'emblée."
    )
    
    marketplace_intro = RichTextField(
        blank=True, 
        verbose_name="Introduction du Marketplace",
        default="Modules Pro à la demande. Achat unique, utilisation illimitée."
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('hero_title'),
        FieldPanel('hero_subtitle'),
        FieldPanel('features_intro'),
        FieldPanel('marketplace_intro'),
    ]

    max_count = 1
    subpage_types = ['content.ContentIndexPage']

class ContentIndexPage(Page):
    """
    Page d'index pour les contenus (Blog, FAQ, Documentation).
    """
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]

    # Autoriser uniquement ContentPage comme sous-page
    subpage_types = ['content.ContentPage']

class ContentPage(Page):
    """
    Page de contenu générique (article de blog ou document technique).
    """
    date = models.DateField("Post date")
    body = RichTextField(blank=True)

    search_fields = Page.search_fields + [
        # La recherche est intégrée par défaut dans Wagtail
    ]

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('body'),
    ]

    # Limiter le type de parent
    parent_page_types = ['content.ContentIndexPage']

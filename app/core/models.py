"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 1.1
Description : Modèles pour les fonctionnalités cœur du portail (Menus, Paramètres).
              Support multilingue via Wagtail i18n.
"""

from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.models import Orderable, TranslatableMixin
from wagtail.snippets.models import register_snippet

class MenuItem(Orderable):
    link_title = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        verbose_name="Titre du lien"
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="URL externe"
    )
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.CASCADE,
        verbose_name="Page interne"
    )
    open_in_new_tab = models.BooleanField(default=False, blank=True, verbose_name="Ouvrir dans un nouvel onglet")

    page = ParentalKey("Menu", related_name="menu_items")

    panels = [
        FieldPanel("link_title"),
        FieldPanel("link_url"),
        PageChooserPanel("link_page"),
        FieldPanel("open_in_new_tab"),
    ]

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_url:
            return self.link_url
        return "#"

    @property
    def title(self):
        if self.link_page and not self.link_title:
            return self.link_page.title
        elif self.link_title:
            return self.link_title
        return "Sans titre"


@register_snippet
class Menu(TranslatableMixin, ClusterableModel):
    """
    Modèle de menu traduisible.
    Utilise TranslatableMixin pour être compatible avec Wagtail Localize.
    """

    title = models.CharField(max_length=100, verbose_name="Nom du menu")
    slug = models.SlugField(help_text="Slug pour identifier ce menu (ex: 'main-menu')")

    panels = [
        MultiFieldPanel([
            FieldPanel("title"),
            FieldPanel("slug"),
        ], heading="Menu"),
        InlinePanel("menu_items", label="Élément de menu")
    ]

    def __str__(self):
        return f"{self.title} ({self.locale})"

    class Meta(TranslatableMixin.Meta):
        verbose_name = "Menu"
        verbose_name_plural = "Menus"
        unique_together = ("slug", "locale")
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_core_menu",
            )
        ]

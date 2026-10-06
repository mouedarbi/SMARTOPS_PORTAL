"""
Fichier : sitemaps.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Classes Sitemap pour la génération dynamique du sitemap.xml SEO.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from catalog.models import Module


class StaticViewSitemap(Sitemap):
    """
    Sitemap pour les vues statiques principales du Portal SMARTOPS.
    """
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        """Noms d'URL des pages fixes."""
        return ['core:home', 'catalog:module_list', 'content:cgv', 'content:confidentialite']

    def location(self, item):
        """Adresse d'une page fixe."""
        return reverse(item)


class ModuleSitemap(Sitemap):
    """
    Sitemap dynamique pour les fiches produits des modules du catalogue.
    """
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        """Modules actifs du catalogue."""
        return Module.objects.filter(is_active=True)

    def location(self, obj):
        """Adresse de la fiche d'un module."""
        return reverse('catalog:module_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        """Date de dernière modification du module."""
        return obj.updated_at

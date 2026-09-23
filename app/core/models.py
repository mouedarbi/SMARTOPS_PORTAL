"""
Fichier : models.py
Projet : Marketplace SMARTOPS
Application : core
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Modèles Django standards pour les Menus.
"""

from django.db import models

class Menu(models.Model):
    title = models.CharField(max_length=100, verbose_name="Nom du menu")
    slug = models.SlugField(unique=True, help_text="Slug pour identifier ce menu (ex: 'main-menu')")

    class Meta:
        verbose_name = "Menu"
        verbose_name_plural = "Menus"

    def __str__(self):
        return self.title

class MenuItem(models.Model):
    link_title = models.CharField(max_length=50, verbose_name="Titre du lien")
    link_url = models.CharField(max_length=500, blank=True, verbose_name="URL")
    open_in_new_tab = models.BooleanField(default=False, blank=True, verbose_name="Ouvrir dans un nouvel onglet")
    sort_order = models.IntegerField(default=0)

    menu = models.ForeignKey(Menu, related_name="items", on_delete=models.CASCADE)

    class Meta:
        ordering = ['sort_order']
        verbose_name = "Élément de menu"
        verbose_name_plural = "Éléments de menu"

    def __str__(self):
        return self.link_title

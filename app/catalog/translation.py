"""
Fichier : translation.py
Projet : Marketplace SMARTOPS
Application : catalog
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Champs traduits (FR/EN/NL) des catégories, modules et packs (django-modeltranslation).
"""

from modeltranslation.translator import register, TranslationOptions
from .models import Category, Module, ModuleBundle

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    """Champs traduits d'une catégorie."""
    fields = ('name', 'slug',)

@register(Module)
class ModuleTranslationOptions(TranslationOptions):
    """Champs traduits d'un module."""
    fields = ('name', 'slug', 'short_description', 'description',)

@register(ModuleBundle)
class ModuleBundleTranslationOptions(TranslationOptions):
    """Champs traduits d'un pack."""
    fields = ('name', 'slug', 'short_description', 'description',)

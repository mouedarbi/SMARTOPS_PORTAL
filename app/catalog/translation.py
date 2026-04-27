from modeltranslation.translator import register, TranslationOptions
from .models import Category, Module, ModuleBundle

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'slug',)

@register(Module)
class ModuleTranslationOptions(TranslationOptions):
    fields = ('name', 'slug', 'short_description', 'description',)

@register(ModuleBundle)
class ModuleBundleTranslationOptions(TranslationOptions):
    fields = ('name', 'slug', 'short_description', 'description',)

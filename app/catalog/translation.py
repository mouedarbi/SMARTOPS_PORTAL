from modeltranslation.translator import register, TranslationOptions
from .models import Category, Module, ModuleBundle

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Module)
class ModuleTranslationOptions(TranslationOptions):
    fields = ('name', 'short_description', 'description',)

@register(ModuleBundle)
class ModuleBundleTranslationOptions(TranslationOptions):
    fields = ('name', 'short_description', 'description',)

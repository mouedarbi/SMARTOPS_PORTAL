from modeltranslation.translator import register, TranslationOptions
from .models import Module

@register(Module)
class ModuleTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

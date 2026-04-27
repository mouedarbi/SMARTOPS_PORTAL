from django.db import models
from django import forms
from catalog.models import Module, Category, ModuleBundle, ModuleVersion, CoreVersion

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            'name_fr', 'name_en', 'name_nl', 
            'slug_fr', 'slug_en', 'slug_nl', 
            'icon'
        ]
        widgets = {
            'name_fr': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900 focus:ring-2 focus:ring-blue-500'}),
            'name_en': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900 focus:ring-2 focus:ring-blue-500'}),
            'name_nl': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900 focus:ring-2 focus:ring-blue-500'}),
            'slug_fr': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500', 'placeholder': 'Généré auto'}),
            'slug_en': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500', 'placeholder': 'Auto-generated'}),
            'slug_nl': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500', 'placeholder': 'Automatisch'}),
            'icon': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = [
            'name_fr', 'name_en', 'name_nl',
            'slug_fr', 'slug_en', 'slug_nl',
            'category', 'price', 'is_active', 'featured_image',
            'short_description_fr', 'short_description_en', 'short_description_nl',
            'description_fr', 'description_en', 'description_nl'
        ]
        widgets = {
            'name_fr': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'name_en': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'name_nl': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'slug_fr': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500'}),
            'slug_en': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500'}),
            'slug_nl': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600'}),
            'short_description_fr': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'short_description_en': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'short_description_nl': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'description_fr': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'description_en': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'description_nl': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
        }

class ModuleVersionForm(forms.ModelForm):
    class Meta:
        model = ModuleVersion
        fields = ['version_number', 'release_date', 'min_core_version', 'max_core_version', 'file', 'changelog']
        widgets = {
            'version_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900', 'placeholder': 'ex: 1.0.0'}),
            'release_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'min_core_version': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'max_core_version': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'file': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'changelog': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
        }

class ModuleBundleForm(forms.ModelForm):
    class Meta:
        model = ModuleBundle
        fields = [
            'name_fr', 'name_en', 'name_nl',
            'slug_fr', 'slug_en', 'slug_nl',
            'modules', 'discount_mode', 'discount_value',
            'start_date', 'end_date', 'is_active', 'featured_image',
            'short_description_fr', 'short_description_en', 'short_description_nl',
            'description_fr', 'description_en', 'description_nl'
        ]
        widgets = {
            'name_fr': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'name_en': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'name_nl': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'slug_fr': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500'}),
            'slug_en': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500'}),
            'slug_nl': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50 text-slate-500'}),
            'modules': forms.CheckboxSelectMultiple(attrs={'class': 'flex flex-wrap gap-4 text-slate-900'}),
            'discount_mode': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'discount_value': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'start_date': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'end_date': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600'}),
            'short_description_fr': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'description_fr': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
        }

class CoreVersionForm(forms.ModelForm):
    class Meta:
        model = CoreVersion
        fields = ['version', 'is_active']
        widgets = {
            'version': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900', 'placeholder': 'ex: 2.4.0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600'}),
        }

from django.contrib.auth import get_user_model
CustomUser = get_user_model()

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'language_preference', 'is_client', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'language_preference': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg text-slate-900'}),
            'is_client': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600'}),
        }

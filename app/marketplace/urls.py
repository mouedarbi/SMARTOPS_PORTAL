"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Configuration globale des routes (URLs) pour le projet Marketplace SMARTOPS.
              Ce fichier contient les patterns d'URLs pour les applications.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('portal-management/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('i18n/', include('django.conf.urls.i18n')), # Ajout pour set_language
]

urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    # Allauth URLs pour l'authentification
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('payments/', include('payments.urls')),
    path('licensing/', include('licensing.urls')),
    path('downloads/', include('downloads.urls')),
    path('content/', include('content.urls')),
    
    # Wagtail Pages (doit être en dernier car il capture tout)
    path('', include(wagtail_urls)),
    prefix_default_language=True
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


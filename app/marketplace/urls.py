"""
Fichier : urls.py
Projet : Marketplace SMARTOPS
Application : marketplace
Auteur : Mohamed Ouedarbi
Version : 2.0
Description : Configuration globale des routes (URLs) pour le projet Marketplace SMARTOPS.
              Version sans Wagtail.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from catalog.sitemaps import StaticViewSitemap, ModuleSitemap
from payments.views import stripe_webhook
from users.views import profile

sitemaps = {
    'static': StaticViewSitemap,
    'modules': ModuleSitemap,
}

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('payments/stripe-webhook/', stripe_webhook, name='stripe_webhook_no_i18n'),
    path('api/licensing/', include('licensing.urls')),
    
    # Routes SEO & Robots
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots_txt"),
]

urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    # Allauth URLs pour l'authentification
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('users.urls')),
    path('catalog/', include('catalog.urls')),
    path('payments/', include('payments.urls')),
    path('licensing/', include('licensing.urls')),
    path('backoffice/', include('backoffice.urls')),
    path('downloads/', include('downloads.urls')),
    path('content/', include('content.urls')),
    prefix_default_language=True
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

import os
import sys
import django
import tarfile
import tempfile
import shutil
from datetime import date

# Configuration Django et ajout du chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from catalog.models import Module, ModuleVersion, CoreVersion

def run():
    print("Début de la génération des packages de plugins placeholders...")
    
    # Récupérer la version Core
    core_version = CoreVersion.objects.first()
    if not core_version:
        print("Création de la version Core 1.0 par défaut...")
        core_version = CoreVersion.objects.create(version="1.0", is_active=True)

    # Répertoire média de destination pour les packages
    packages_dir = "/root/smartops_portal/SMARTOPS_PORTAL/app/media/modules/packages"
    os.makedirs(packages_dir, exist_ok=True)

    # Liste des modules et configurations spécifiques pour les placeholders
    modules_config = [
        {
            "slug": "contrats-de-maintenance",
            "name": "Contrats de Maintenance",
            "label": "Contrats de Maintenance",
            "icon": "la-file-contract",
            "desc": "Gestion et automatisation des contrats de maintenance récurrents."
        },
        {
            "slug": "gestion-de-la-flotte-vehicules",
            "name": "Gestion de la Flotte Véhicules",
            "label": "Flotte Véhicules",
            "icon": "la-car",
            "desc": "Suivi et attribution de la flotte de véhicules de maintenance."
        },
        {
            "slug": "hrm-absences-redistribution-de-charge",
            "name": "HRM - Absences & Redistribution de Charge",
            "label": "Planning & RH",
            "icon": "la-users-cog",
            "desc": "Gestion des absences, congés et répartition de la charge."
        },
        {
            "slug": "signature-electronique-rapports-pdf",
            "name": "Signature Électronique & Rapports PDF",
            "label": "Signature & Rapports",
            "icon": "la-signature",
            "desc": "Signature électronique des bons d'intervention et rapports PDF."
        },
        {
            "slug": "iot-alertes-predictives",
            "name": "IoT & Alertes Prédictives",
            "label": "IoT & Alertes",
            "icon": "la-broadcast-tower",
            "desc": "Surveillance par capteurs connectés et génération d'alertes."
        },
        {
            "slug": "stock-pieces-detachees",
            "name": "Stock & Pièces Détachées",
            "label": "Stock & Pièces",
            "icon": "la-boxes",
            "desc": "Suivi de l'inventaire des pièces détachées et alertes."
        },
        {
            "slug": "localisation-des-sites",
            "name": "Localisation des sites",
            "label": "Localisation des Sites",
            "icon": "la-map-marked-alt",
            "desc": "Cartographie interactive et géolocalisation des sites."
        }
    ]

    for config in modules_config:
        slug = config["slug"]
        module = Module.objects.filter(slug_fr=slug).first()
        if not module:
            print(f"Erreur : Le module '{slug}' n'existe pas en base de données.")
            continue
            
        package_name = slug.replace('-', '_')
        print(f"Génération du package pour : {module.name} ({package_name})...")
        
        # 1. Créer une arborescence temporaire pour ce plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer le répertoire de l'application python
            app_dir = os.path.join(temp_dir, package_name)
            os.makedirs(app_dir)
            
            # pyproject.toml
            pyproject_content = f"""[project]
name = "smartops-plugin-{slug}"
version = "1.0.0"
dependencies = ["pluggy>=1.0.0"]

[project.entry-points."smartops.plugins"]
{package_name} = "{package_name}.hookimpls:plugin_implementation"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
"""
            with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
                f.write(pyproject_content)
                
            # app/__init__.py
            with open(os.path.join(app_dir, "__init__.py"), "w") as f:
                f.write("")
                
            # app/hookimpls.py
            hookimpls_content = f"""import pluggy
hookimpl = pluggy.HookimplMarker("smartops")

class PlaceholderPlugin:
    @hookimpl
    def register_menu_items(self):
        return [{{
            "label": "{config["label"]}",
            "url": "/app/{package_name}/",
            "icon": "{config["icon"]}"
        }}]

plugin_implementation = PlaceholderPlugin()
"""
            with open(os.path.join(app_dir, "hookimpls.py"), "w") as f:
                f.write(hookimpls_content)
                
            # app/urls.py
            urls_content = f"""from django.urls import path
from . import views
urlpatterns = [
    path('', views.index_view, name='index'),
]
"""
            with open(os.path.join(app_dir, "urls.py"), "w") as f:
                f.write(urls_content)
                
            # app/views.py
            views_content = f"""from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index_view(request):
    return render(request, '{package_name}/index.html', {{
        'page_title': '{config["name"]}',
        'description': '{config["desc"]}'
    }})
"""
            with open(os.path.join(app_dir, "views.py"), "w") as f:
                f.write(views_content)
                
            # app/templates/app/index.html
            templates_dir = os.path.join(app_dir, "templates", package_name)
            os.makedirs(templates_dir)
            
            html_content = f"""{{% extends "base.html" %}}

{{% block title %}}{config["name"]} | SMARTOPS{{% endblock %}}
{{% block page_title %}}{config["name"]}{{% endblock %}}

{{% block content %}}
<div class="max-w-4xl mx-auto bg-white rounded-3xl border border-slate-100 p-8 text-center space-y-6 shadow-sm">
    <div class="inline-flex items-center justify-center w-20 h-20 bg-blue-50 text-blue-600 rounded-full mb-2">
        <i class="las {config["icon"]} text-5xl"></i>
    </div>
    
    <div class="space-y-2">
        <h1 class="text-2xl font-black text-slate-800">Module Premium Actif</h1>
        <p class="text-slate-500 font-medium max-w-lg mx-auto">
            {config["desc"]}
        </p>
    </div>
    
    <div class="p-6 bg-slate-50 rounded-2xl border border-slate-100 max-w-md mx-auto">
        <span class="text-xs font-bold uppercase tracking-widest text-blue-600 block mb-1">Statut d'intégration</span>
        <span class="text-sm font-semibold text-slate-600">Version de démonstration TFE (Placeholder actif)</span>
    </div>
    
    <div class="pt-4">
        <a href="javascript:history.back()" class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold px-6 py-2.5 rounded-xl text-sm transition">
            Retour
        </a>
    </div>
</div>
{{% endblock %}}
"""
            with open(os.path.join(templates_dir, "index.html"), "w") as f:
                f.write(html_content)

            # 2. Compacter le dossier temporaire en .tar.gz dans le dossier média
            archive_filename = f"{package_name}_placeholder.tar.gz"
            archive_path = os.path.join(packages_dir, archive_filename)
            
            # Supprimer l'ancienne archive si elle existe
            if os.path.exists(archive_path):
                os.remove(archive_path)
                
            with tarfile.open(archive_path, "w:gz") as tar:
                # Ajouter pyproject.toml
                tar.add(os.path.join(temp_dir, "pyproject.toml"), arcname="pyproject.toml")
                # Ajouter le dossier de l'application
                tar.add(app_dir, arcname=package_name)
                
            print(f"Archive créée : {archive_filename}")
            
            # 3. Créer ou mettre à jour la version du module en base de données
            version_rel_path = f"modules/packages/{archive_filename}"
            
            # Nettoyer les versions précédentes pour repartir à propre
            ModuleVersion.objects.filter(module=module).delete()
            
            ModuleVersion.objects.create(
                module=module,
                version_number="1.0.0",
                release_date=date.today(),
                min_core_version=core_version,
                changelog="Version placeholder pour démonstration de TFE.",
                file=version_rel_path
            )
            print(f"Base de données mise à jour : {module.name} v1.0.0 -> {version_rel_path}")

    print("Génération de tous les packages placeholders complétée avec succès !")

if __name__ == '__main__':
    run()

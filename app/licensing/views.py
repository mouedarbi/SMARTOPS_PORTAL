"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.5
Description : API de validation des licences et service de téléchargement sécurisé des packages modules.
"""

import json
from django.http import JsonResponse, FileResponse, Http404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import License
from catalog.models import ModuleVersion

@method_decorator(csrf_exempt, name='dispatch')
class ValidateLicenseAPI(View):
    """
    API permettant au SMARTOPS CORE de valider une clé de licence.
    Endpoint: POST /api/licensing/validate/
    Paramètres: {'license_key': 'UUID'}
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            key = data.get('license_key')
            client_uuid = data.get('installation_uuid') # Nouvel UUID envoyé par le client
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"success": False, "error": "Données JSON invalides."}, status=400)

        if not key:
            return JsonResponse({"success": False, "error": "Clé de licence manquante."}, status=400)

        try:
            # Recherche de la licence active
            license_obj = License.objects.get(license_key=key, is_active=True)
            module = license_obj.module
            
            # --- LOGIQUE HARDWARE BINDING ---
            if not client_uuid:
                return JsonResponse({"success": False, "error": "ID Installation (UUID) manquant pour cette machine."}, status=400)

            from .models import Installation
            
            # Récupère ou crée l'installation pour cet UUID et cet utilisateur
            installation, created = Installation.objects.get_or_create(
                installation_uuid=client_uuid,
                user=license_obj.user
            )

            if license_obj.installation:
                # La licence est déjà liée à une machine
                if str(license_obj.installation.installation_uuid) != str(client_uuid):
                    return JsonResponse({
                        "success": False, 
                        "error": "Cette licence est déjà activée sur un autre système SMARTOPS."
                    }, status=403)
            else:
                # Première activation : on lie la licence à cette installation
                license_obj.installation = installation
                license_obj.save()
            # --------------------------------
            
            # Récupération de la dernière version du module
            latest_version = module.versions.order_by('-release_date', '-version_number').first()
            
            if not latest_version:
                return JsonResponse({"success": False, "error": "Aucun package disponible pour ce module."}, status=404)

            # Construction de l'URL de téléchargement
            download_url = request.build_absolute_uri(
                reverse('download_module_package', kwargs={'license_key': key})
            )

            # Incrémentation du compteur d'activations
            license_obj.activation_count += 1
            license_obj.save()

            return JsonResponse({
                "success": True,
                "plugin_slug": module.slug,
                "plugin_name": module.name,
                "version": latest_version.version_number,
                "package_name": module.slug.replace('-', '_'),
                "download_url": download_url
            })

        except License.DoesNotExist:
            return JsonResponse({"success": False, "error": "Clé de licence invalide ou expirée."}, status=403)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

class DownloadModulePackageAPI(View):
    """
    Sert le fichier du module après vérification de la licence.
    Endpoint: GET /api/licensing/download/<license_key>/
    """
    def get(self, request, license_key, *args, **kwargs):
        license_obj = get_object_or_404(License, license_key=license_key, is_active=True)
        module = license_obj.module
        
        latest_version = module.versions.order_by('-release_date', '-version_number').first()
        
        if not latest_version or not latest_version.file:
            raise Http404("Fichier non trouvé pour ce module.")

        # Retourne le fichier
        response = FileResponse(latest_version.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{module.slug}_{latest_version.version_number}.tar.gz"'
        return response

@method_decorator(csrf_exempt, name='dispatch')
class SyncInstallationAPI(View):
    """
    API de télémétrie et synchronisation.
    Permet au Portail de savoir quelles installations sont actives 
    et de renvoyer les mises à jour disponibles.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            client_uuid = data.get('installation_uuid')
            if not client_uuid:
                return JsonResponse({"success": False, "error": "UUID manquant."}, status=400)
            
            from .models import Installation
            from catalog.models import Module
            from django.utils import timezone
            
            # 1. Mise à jour ou Création de l'installation (Télémétrie)
            # On utilise get_or_create puis on modifie manuellement pour forcer le save() et le timestamp
            installation, created = Installation.objects.get_or_create(
                installation_uuid=client_uuid
            )
            
            installation.company_name = data.get('company_name', installation.company_name)
            installation.core_version = data.get('core_version', installation.core_version)
            installation.last_sync = timezone.now() # On force la date actuelle
            installation.save()

            # 2. Vérification des mises à jour pour les modules envoyés
            installed_modules = data.get('installed_modules', [])
            updates = []
            
            for mod_data in installed_modules:
                slug = mod_data.get('slug')
                local_version = mod_data.get('version')
                
                try:
                    module = Module.objects.get(slug=slug)
                    latest = module.versions.order_by('-release_date', '-version_number').first()
                    
                    if latest and str(latest.version_number) != str(local_version):
                        updates.append({
                            "slug": slug,
                            "name": module.name,
                            "current_version": local_version,
                            "new_version": latest.version_number,
                        })
                except Module.DoesNotExist:
                    continue

            return JsonResponse({
                "success": True,
                "message": "Synchronisation réussie.",
                "updates_available": len(updates) > 0,
                "module_updates": updates
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

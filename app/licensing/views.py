"""
Fichier : views.py
Projet : Marketplace SMARTOPS
Application : licensing
Auteur : Mohamed Ouedarbi
Version : 1.5
Description : API de validation des licences et service de téléchargement sécurisé des packages modules.
"""

import json
import logging
import secrets
from urllib.parse import quote

from django.conf import settings
from django.core import signing
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from .models import License
from catalog.models import ModuleVersion

audit_logger = logging.getLogger('audit')

@method_decorator(csrf_exempt, name='dispatch')
class ValidateLicenseAPI(View):
    """
    API permettant au SMARTOPS CORE de valider une clé de licence.
    Endpoint: POST /api/licensing/validate/
    Paramètres: {'license_key': 'UUID'}
    """
    def post(self, request, *args, **kwargs):
        """
        Valide la clé, la lie à l'installation et renvoie le module et son lien de
        téléchargement (quota d'activations et liaison à une seule installation).
        """
        try:
            data = json.loads(request.body)
            key = data.get('license_key')
            client_uuid = data.get('installation_uuid')
        except (json.JSONDecodeError, AttributeError):
            audit_logger.warning("API LICENSE VALIDATION FAILED: Invalid JSON payload.")
            return JsonResponse({"success": False, "error": "Données JSON invalides."}, status=400)

        if not key:
            audit_logger.warning(f"API LICENSE VALIDATION FAILED: Missing license key (Request from installation {client_uuid}).")
            return JsonResponse({"success": False, "error": "Clé de licence manquante."}, status=400)

        try:
            # Recherche de la licence active
            license_obj = License.objects.get(license_key=key, is_active=True)
            module = license_obj.module

            # Ressaisie de la clé sur l'installation à laquelle elle est déjà liée
            # (ex. réinstallation après un échec) : ce n'est pas une nouvelle activation.
            already_bound_here = (
                license_obj.installation is not None
                and str(license_obj.installation.installation_uuid) == str(client_uuid)
            )

            # Vérification du quota d'activations autorisées
            if not already_bound_here and license_obj.activation_count >= license_obj.max_activations:
                audit_logger.warning(
                    f"API LICENSE VALIDATION FAILED: Quota exceeded for key {key} ({license_obj.activation_count}/{license_obj.max_activations}). Installation {client_uuid}."
                )
                return JsonResponse({
                    "success": False, 
                    "error": "Le quota d'activations autorisées pour cette licence est atteint."
                }, status=403)
            
            # --- LOGIQUE HARDWARE BINDING ---
            if not client_uuid:
                audit_logger.warning(f"API LICENSE VALIDATION FAILED: Missing installation UUID for key {key}.")
                return JsonResponse({"success": False, "error": "ID Installation (UUID) manquant pour cette machine."}, status=400)

            # Une seule licence par module et par installation
            if not already_bound_here and License.objects.filter(
                module=module,
                is_active=True,
                installation__installation_uuid=client_uuid,
            ).exclude(pk=license_obj.pk).exists():
                audit_logger.warning(
                    f"API LICENSE VALIDATION FAILED: Module {module.name} is already activated on installation "
                    f"{client_uuid} with another license (Key {key})."
                )
                return JsonResponse({
                    "success": False,
                    "error": "Ce module est déjà activé sur cette installation avec une autre licence."
                }, status=403)

            from .models import Installation
            
            # Récupère d'abord l'installation par son UUID unique
            # (elle a pu être créée anonymement lors d'une synchro précédente)
            installation, created = Installation.objects.get_or_create(
                installation_uuid=client_uuid
            )
            
            # Si l'installation n'avait pas de propriétaire, on lui affecte celui de la licence
            if not installation.user:
                installation.user = license_obj.user
                installation.save()

            if license_obj.installation:
                # La licence est déjà liée à une machine
                if str(license_obj.installation.installation_uuid) != str(client_uuid):
                    audit_logger.warning(
                        f"API LICENSE VALIDATION FAILED: Key {key} is already bound to installation "
                        f"{license_obj.installation.installation_uuid} (Request from installation {client_uuid})."
                    )
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
                audit_logger.error(f"API LICENSE VALIDATION FAILED: No package version available for module {module.name} (Key {key}).")
                return JsonResponse({"success": False, "error": "Aucun package disponible pour ce module."}, status=404)

            # Construction de l'URL de téléchargement de manière sécurisée
            download_url = request.build_absolute_uri(
                reverse('download_module_package', kwargs={'license_key': key})
            )

            # Incrémentation du compteur d'activations
            if not already_bound_here:
                license_obj.activation_count += 1
                license_obj.save()

            audit_logger.info(
                f"API LICENSE VALIDATION SUCCESS: Key {key} successfully validated and bound to installation {client_uuid} (User: {license_obj.user.username}, Module: {module.name})."
            )

            return JsonResponse({
                "success": True,
                "plugin_slug": module.slug_fr,
                "plugin_name": module.name,
                "version": latest_version.version_number,
                "min_core_version": latest_version.min_core_version.version,
                "max_core_version": latest_version.max_core_version.version if latest_version.max_core_version else None,
                "package_name": module.slug_fr.replace('-', '_'),
                "download_url": download_url
            })

        except License.DoesNotExist:
            audit_logger.warning(
                f"API LICENSE VALIDATION FAILED: Key {key} is invalid or expired (Request from installation {client_uuid})."
            )
            return JsonResponse({"success": False, "error": "Clé de licence invalide ou expirée."}, status=403)
        except Exception as e:
            audit_logger.exception(f"API LICENSE VALIDATION ERROR: Unexpected error for key {key} (installation {client_uuid}).")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

class DownloadModulePackageAPI(View):
    """
    Sert le fichier du module après vérification de la licence.
    Endpoint: GET /api/licensing/download/<license_key>/
    """
    def get(self, request, license_key, *args, **kwargs):
        """Sert le paquet de la dernière version du module de la licence active."""
        license_obj = License.objects.filter(license_key=license_key, is_active=True).select_related('module', 'user').first()
        if license_obj is None:
            audit_logger.warning(f"API PACKAGE DOWNLOAD FAILED: License {license_key} is invalid or inactive.")
            raise Http404("Licence invalide.")
        module = license_obj.module

        latest_version = module.versions.order_by('-release_date', '-version_number').first()

        if not latest_version or not latest_version.file:
            audit_logger.error(f"API PACKAGE DOWNLOAD FAILED: No package file for module {module.name} (License {license_key}).")
            raise Http404("Fichier non trouvé pour ce module.")

        # Log before download
        audit_logger.info(
            f"API PACKAGE DOWNLOAD: License {license_key} downloading package for module {module.name} (v{latest_version.version_number}) (User: {license_obj.user.username})."
        )

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
        """
        Enregistre l'installation (télémétrie) et renvoie les mises à jour disponibles
        pour ses modules.
        """
        try:
            data = json.loads(request.body)
            client_uuid = data.get('installation_uuid')
            if not client_uuid:
                audit_logger.warning("API SYNC FAILED: Missing installation UUID.")
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

            audit_logger.info(
                f"API SYNC SUCCESS: Installation {client_uuid} ({installation.company_name or '-'}, Core {installation.core_version or '-'}) "
                f"synchronized with {len(installed_modules)} module(s); {len(updates)} update(s) available."
            )
            return JsonResponse({
                "success": True,
                "message": "Synchronisation réussie.",
                "updates_available": len(updates) > 0,
                "module_updates": updates
            })

        except Exception as e:
            audit_logger.exception("API SYNC ERROR: Unexpected error during installation synchronization.")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ReleaseLicenseAPI(View):
    """
    API permettant de libérer une licence (Désactivation).
    Endpoint: POST /api/licensing/release/
    """
    def post(self, request, *args, **kwargs):
        """Libère la licence de l'installation qui la demande (désinstallation du module)."""
        try:
            data = json.loads(request.body)
            key = data.get('license_key')
            client_uuid = data.get('installation_uuid')
        except Exception as e:
            audit_logger.warning("API LICENSE RELEASE FAILED: Invalid JSON payload.")
            return JsonResponse({"success": False, "error": "Données invalides."}, status=400)

        if not key or not client_uuid:
            audit_logger.warning(f"API LICENSE RELEASE FAILED: Missing license key or installation UUID (Key {key}, installation {client_uuid}).")
            return JsonResponse({"success": False, "error": "UUIDs manquants (Licence ou Installation)."}, status=400)

        try:
            # Recherche par UUID de licence ET UUID de machine via la relation
            license_obj = License.objects.get(
                license_key=key,
                installation__installation_uuid=client_uuid
            )

            # Libération immédiate
            license_obj.installation = None
            license_obj.activation_count = 0
            license_obj.save()
            
            audit_logger.info(
                f"API LICENSE RELEASE SUCCESS: Key {key} released from installation {client_uuid} (User: {license_obj.user.username}, Module: {license_obj.module.name})."
            )
            
            return JsonResponse({"success": True, "message": "Licence libérée avec succès."})
                
        except License.DoesNotExist:
            audit_logger.warning(
                f"API LICENSE RELEASE FAILED: No matching license found for key {key} and installation {client_uuid}."
            )
            return JsonResponse({"success": False, "error": "Correspondance UUID Licence/Installation introuvable."}, status=404)
        except Exception as e:
            audit_logger.exception(f"API LICENSE RELEASE ERROR: Unexpected error for key {key} (installation {client_uuid}).")
            return JsonResponse({"success": False, "error": str(e)}, status=500)


MOBILE_APK_SALT = 'licensing.mobile-apk'


@method_decorator(csrf_exempt, name='dispatch')
class MobileApkLinkAPI(View):
    """
    Lien de téléchargement de l'APK du module SmartOps Mobile, demandé par le Core.
    Endpoint: POST /api/licensing/mobile-apk/link/
    Paramètres: {'license_key': 'UUID', 'installation_uuid': 'UUID'}
    Le lien est signé, différent à chaque demande et valable MOBILE_APK_LINK_MAX_AGE secondes.
    """
    def post(self, request, *args, **kwargs):
        """
        Renvoie un lien signé valable MOBILE_APK_LINK_MAX_AGE secondes, si la licence est
        active et liée à l'installation qui fait la demande.
        """
        try:
            data = json.loads(request.body)
            key = data.get('license_key')
            client_uuid = data.get('installation_uuid')
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"success": False, "error": "Données JSON invalides."}, status=400)

        license_obj = License.objects.filter(
            license_key=key, is_active=True, installation__isnull=False,
        ).select_related('module', 'installation', 'user').first() if key and client_uuid else None

        # La licence doit être active et liée à l'installation qui fait la demande.
        if license_obj is None or str(license_obj.installation.installation_uuid) != str(client_uuid):
            audit_logger.warning(f"API MOBILE APK LINK FAILED: invalid license or installation (installation {client_uuid}).")
            return JsonResponse({"success": False, "error": "Licence invalide ou non activée sur cette installation."}, status=403)

        version = license_obj.module.versions.order_by('-release_date', '-version_number').first()
        if version is None or not version.mobile_apk:
            audit_logger.error(f"API MOBILE APK LINK FAILED: no APK for module {license_obj.module.name} (License #{license_obj.pk}).")
            return JsonResponse({"success": False, "error": "Aucune application mobile disponible pour ce module."}, status=404)

        token = signing.dumps(
            {'l': license_obj.pk, 'v': version.pk, 'n': secrets.token_hex(4)}, salt=MOBILE_APK_SALT, compress=True,
        )
        audit_logger.info(
            f"API MOBILE APK LINK: link issued for module {license_obj.module.name} v{version.version_number} "
            f"(License #{license_obj.pk}, installation {client_uuid}, user {license_obj.user.username})."
        )
        return JsonResponse({
            "success": True,
            "url": request.build_absolute_uri(reverse('mobile_apk_download', kwargs={'token': token})),
            "expires_in": settings.MOBILE_APK_LINK_MAX_AGE,
            "version": version.version_number,
            "size": version.mobile_apk.size,
        })


class MobileApkDownloadAPI(View):
    """
    Téléchargement de l'APK par un lien signé (MobileApkLinkAPI).
    Endpoint: GET /api/licensing/mobile-apk/<token>/
    En production, le fichier est envoyé par nginx (X-Accel-Redirect) : le worker n'est pas occupé.
    """
    def get(self, request, token, *args, **kwargs):
        """Vérifie le lien signé et la licence, puis envoie l'APK (par nginx en production)."""
        try:
            data = signing.loads(token, salt=MOBILE_APK_SALT, max_age=settings.MOBILE_APK_LINK_MAX_AGE)
        except signing.SignatureExpired:
            audit_logger.warning("API MOBILE APK DOWNLOAD FAILED: expired link.")
            return HttpResponse("Ce lien de téléchargement a expiré. Demandez-en un nouveau depuis le Core.", status=410, content_type='text/plain; charset=utf-8')
        except signing.BadSignature:
            raise Http404("Lien invalide.")

        license_obj = License.objects.filter(pk=data.get('l'), is_active=True, installation__isnull=False).first()
        version = ModuleVersion.objects.filter(pk=data.get('v')).first()
        if license_obj is None or version is None or version.module_id != license_obj.module_id or not version.mobile_apk:
            audit_logger.warning(f"API MOBILE APK DOWNLOAD FAILED: license or APK no longer available (License #{data.get('l')}).")
            raise Http404("Fichier non disponible.")

        audit_logger.info(f"API MOBILE APK DOWNLOAD: v{version.version_number} (License #{license_obj.pk}).")
        filename = f"smartops-technicien-{version.version_number}.apk"
        content_type = 'application/vnd.android.package-archive'
        if settings.USE_X_ACCEL_REDIRECT:
            response = HttpResponse(content_type=content_type)
            response['X-Accel-Redirect'] = settings.PRIVATE_MEDIA_X_ACCEL_PREFIX + quote(version.mobile_apk.name)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return FileResponse(version.mobile_apk.open('rb'), as_attachment=True, filename=filename, content_type=content_type)

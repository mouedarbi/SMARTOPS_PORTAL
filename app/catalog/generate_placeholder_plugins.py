"""
Génère les archives des modules de démonstration du catalogue.

Les sources des modules sont désormais maintenues dans le dépôt SMARTOPS_MODULES, dont
`tools/build_archive.py` produit les archives publiées sur le Portal. Ce script reste utilisable pour
régénérer des archives de démonstration ; il n'est plus la référence.
"""
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

from django.conf import settings
from catalog.models import Module, ModuleVersion, CoreVersion

PACKAGE_VERSION = "1.0.1"

# ---------------------------------------------------------------------------
# Gabarit HTML commun : bandeau "Démonstration" + contenu spécifique au module.
# Pas de f-string ici : on utilise des jetons __XXX__ remplacés ensuite, pour
# ne jamais entrer en conflit avec la syntaxe Django {% %} / {{ }}.
# ---------------------------------------------------------------------------
BASE_TEMPLATE = """{% extends "base.html" %}

{% block title %}__NAME__ | SMARTOPS{% endblock %}
{% block page_title %}__NAME__{% endblock %}

{% block content %}
<div class="max-w-6xl mx-auto space-y-6">
    <div class="flex items-start justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-4">
            <div class="h-14 w-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center flex-shrink-0">
                <i class="las __ICON__ text-3xl"></i>
            </div>
            <div>
                <h1 class="text-xl font-black text-slate-800">__NAME__</h1>
                <p class="text-slate-500 font-medium text-sm">__DESC__</p>
            </div>
        </div>
        <span class="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-50 text-amber-600 border border-amber-100 rounded-full text-[11px] font-black uppercase tracking-wider flex-shrink-0">
            <i class="las la-flask"></i> Démonstration — données fictives
        </span>
    </div>

__CONTENT__
</div>
{% endblock %}
"""

ACTION_JS = "alert('Fonctionnalité de démonstration — non connectée à une base de données.')"

# ---------------------------------------------------------------------------
# Fragments spécifiques par module (données 100% statiques, aucun modèle).
# ---------------------------------------------------------------------------

CONTENT_CONTRACTS = """
<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Contrats actifs</p>
        <p class="text-2xl font-black text-slate-800">18</p>
    </div>
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">À renouveler (30j)</p>
        <p class="text-2xl font-black text-amber-600">3</p>
    </div>
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Échéances générées ce mois</p>
        <p class="text-2xl font-black text-slate-800">7</p>
    </div>
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Taux de reconduction</p>
        <p class="text-2xl font-black text-emerald-600">92%</p>
    </div>
</div>

<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Contrats en cours</h2>
        <button onclick="ACTION_JS" class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold px-4 py-2 rounded-xl text-xs transition">
            <i class="las la-plus"></i> Nouveau contrat
        </button>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="px-6 py-3 font-bold">Client</th>
                    <th class="px-6 py-3 font-bold">Équipement</th>
                    <th class="px-6 py-3 font-bold">Fréquence</th>
                    <th class="px-6 py-3 font-bold">Prochaine échéance</th>
                    <th class="px-6 py-3 font-bold">Statut</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Atelier Dupont SA</td>
                    <td class="px-6 py-4 text-slate-500">Compresseur CP-12</td>
                    <td class="px-6 py-4 text-slate-500">Trimestriel</td>
                    <td class="px-6 py-4 text-slate-500">15/10/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Actif</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Boulangerie Lemoine</td>
                    <td class="px-6 py-4 text-slate-500">Four industriel FX-3</td>
                    <td class="px-6 py-4 text-slate-500">Mensuel</td>
                    <td class="px-6 py-4 text-slate-500">02/10/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Actif</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Garage Meunier</td>
                    <td class="px-6 py-4 text-slate-500">Pont élévateur PE-2</td>
                    <td class="px-6 py-4 text-slate-500">2x / an</td>
                    <td class="px-6 py-4 text-slate-500">28/11/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">À renouveler</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Clinique Vetalis</td>
                    <td class="px-6 py-4 text-slate-500">Groupe froid GF-9</td>
                    <td class="px-6 py-4 text-slate-500">Mensuel</td>
                    <td class="px-6 py-4 text-slate-500">05/10/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Actif</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Hôtel Bellevue</td>
                    <td class="px-6 py-4 text-slate-500">Chaudière collective</td>
                    <td class="px-6 py-4 text-slate-500">1x / an</td>
                    <td class="px-6 py-4 text-slate-500">12/01/2027</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Actif</span></td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
""".replace("ACTION_JS", ACTION_JS)

CONTENT_FLEET = """
<div class="grid grid-cols-1 md:grid-cols-3 gap-5">
    <div class="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
            <div class="h-11 w-11 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center"><i class="las la-truck-pickup text-xl"></i></div>
            <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Disponible</span>
        </div>
        <div>
            <p class="font-bold text-slate-800">Camionnette Renault Trafic</p>
            <p class="text-xs text-slate-400 font-mono">1-ABC-123</p>
        </div>
        <div class="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-50">
            <p><i class="las la-tachometer-alt mr-1"></i>84 320 km</p>
            <p><i class="las la-user mr-1"></i>Julien Perrin</p>
            <p><i class="las la-calendar-check mr-1"></i>Contrôle technique : 03/11/2026</p>
        </div>
    </div>
    <div class="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
            <div class="h-11 w-11 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center"><i class="las la-shuttle-van text-xl"></i></div>
            <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-blue-50 text-blue-600 border border-blue-100">En intervention</span>
        </div>
        <div>
            <p class="font-bold text-slate-800">Fourgon Peugeot Boxer</p>
            <p class="text-xs text-slate-400 font-mono">1-DEF-456</p>
        </div>
        <div class="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-50">
            <p><i class="las la-tachometer-alt mr-1"></i>129 870 km</p>
            <p><i class="las la-user mr-1"></i>Sofia Benali</p>
            <p><i class="las la-calendar-check mr-1"></i>Contrôle technique : 18/12/2026</p>
        </div>
    </div>
    <div class="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
            <div class="h-11 w-11 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center"><i class="las la-car text-xl"></i></div>
            <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">Maintenance</span>
        </div>
        <div>
            <p class="font-bold text-slate-800">Citroën Berlingo</p>
            <p class="text-xs text-slate-400 font-mono">1-GHI-789</p>
        </div>
        <div class="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-50">
            <p><i class="las la-tachometer-alt mr-1"></i>201 040 km</p>
            <p><i class="las la-user mr-1"></i>Non assigné</p>
            <p><i class="las la-calendar-check mr-1"></i>Contrôle technique : 09/09/2026 (dépassé)</p>
        </div>
    </div>
</div>

<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Flotte complète</h2>
        <button onclick="ACTION_JS" class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold px-4 py-2 rounded-xl text-xs transition">
            <i class="las la-plus"></i> Ajouter un véhicule
        </button>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="px-6 py-3 font-bold">Véhicule</th>
                    <th class="px-6 py-3 font-bold">Plaque</th>
                    <th class="px-6 py-3 font-bold">Technicien assigné</th>
                    <th class="px-6 py-3 font-bold">Kilométrage</th>
                    <th class="px-6 py-3 font-bold">Statut</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Renault Trafic</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">1-ABC-123</td>
                    <td class="px-6 py-4 text-slate-500">Julien Perrin</td>
                    <td class="px-6 py-4 text-slate-500">84 320 km</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Disponible</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Peugeot Boxer</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">1-DEF-456</td>
                    <td class="px-6 py-4 text-slate-500">Sofia Benali</td>
                    <td class="px-6 py-4 text-slate-500">129 870 km</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-blue-50 text-blue-600 border border-blue-100">En intervention</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Citroën Berlingo</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">1-GHI-789</td>
                    <td class="px-6 py-4 text-slate-500">Non assigné</td>
                    <td class="px-6 py-4 text-slate-500">201 040 km</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">Maintenance</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Ford Transit</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">1-JKL-321</td>
                    <td class="px-6 py-4 text-slate-500">Karim Toussaint</td>
                    <td class="px-6 py-4 text-slate-500">57 610 km</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Disponible</span></td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
""".replace("ACTION_JS", ACTION_JS)

CONTENT_HRM = """
<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Absences en cours &amp; redistribution de charge</h2>
        <button onclick="ACTION_JS" class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold px-4 py-2 rounded-xl text-xs transition">
            <i class="las la-plus"></i> Déclarer une absence
        </button>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="px-6 py-3 font-bold">Technicien</th>
                    <th class="px-6 py-3 font-bold">Type</th>
                    <th class="px-6 py-3 font-bold">Période</th>
                    <th class="px-6 py-3 font-bold">Charge redistribuée à</th>
                    <th class="px-6 py-3 font-bold">Statut</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Karim Toussaint</td>
                    <td class="px-6 py-4 text-slate-500">Congés payés</td>
                    <td class="px-6 py-4 text-slate-500">21/09 → 25/09/2026</td>
                    <td class="px-6 py-4 text-slate-500">Sofia Benali (+4 tickets)</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-blue-50 text-blue-600 border border-blue-100">Validée</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Sofia Benali</td>
                    <td class="px-6 py-4 text-slate-500">Arrêt maladie</td>
                    <td class="px-6 py-4 text-slate-500">18/09 → 20/09/2026</td>
                    <td class="px-6 py-4 text-slate-500">Julien Perrin (+2 tickets)</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">En cours</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Julien Perrin</td>
                    <td class="px-6 py-4 text-slate-500">Formation</td>
                    <td class="px-6 py-4 text-slate-500">30/09/2026</td>
                    <td class="px-6 py-4 text-slate-500">Karim Toussaint (+1 ticket)</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-100 text-slate-500 border border-slate-200">Planifiée</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Nadia Fontaine</td>
                    <td class="px-6 py-4 text-slate-500">Congés payés</td>
                    <td class="px-6 py-4 text-slate-500">05/10 → 12/10/2026</td>
                    <td class="px-6 py-4 text-slate-500">Répartition équipe (3 techniciens)</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-100 text-slate-500 border border-slate-200">Planifiée</span></td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Charge moyenne équipe</p>
        <p class="text-2xl font-black text-slate-800">78%</p>
    </div>
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Techniciens absents aujourd'hui</p>
        <p class="text-2xl font-black text-amber-600">2</p>
    </div>
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Tickets redistribués ce mois</p>
        <p class="text-2xl font-black text-slate-800">11</p>
    </div>
</div>
""".replace("ACTION_JS", ACTION_JS)

CONTENT_SIGNATURE = """
<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Rapports d'intervention</h2>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="px-6 py-3 font-bold">Rapport</th>
                    <th class="px-6 py-3 font-bold">Client</th>
                    <th class="px-6 py-3 font-bold">Date intervention</th>
                    <th class="px-6 py-3 font-bold">Signature</th>
                    <th class="px-6 py-3 font-bold text-right">Action</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">RAP-2026-0412</td>
                    <td class="px-6 py-4 text-slate-500">Atelier Dupont SA</td>
                    <td class="px-6 py-4 text-slate-500">08/09/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Signé</span></td>
                    <td class="px-6 py-4 text-right"><button onclick="ACTION_JS" class="text-blue-600 hover:text-blue-700 font-bold text-xs"><i class="las la-file-download mr-1"></i>PDF</button></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">RAP-2026-0413</td>
                    <td class="px-6 py-4 text-slate-500">Clinique Vetalis</td>
                    <td class="px-6 py-4 text-slate-500">09/09/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">En attente</span></td>
                    <td class="px-6 py-4 text-right"><button onclick="ACTION_JS" class="text-white bg-slate-800 hover:bg-slate-900 font-bold text-xs px-3 py-1.5 rounded-lg"><i class="las la-signature mr-1"></i>Signer</button></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">RAP-2026-0414</td>
                    <td class="px-6 py-4 text-slate-500">Hôtel Bellevue</td>
                    <td class="px-6 py-4 text-slate-500">10/09/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Signé</span></td>
                    <td class="px-6 py-4 text-right"><button onclick="ACTION_JS" class="text-blue-600 hover:text-blue-700 font-bold text-xs"><i class="las la-file-download mr-1"></i>PDF</button></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">RAP-2026-0415</td>
                    <td class="px-6 py-4 text-slate-500">Garage Meunier</td>
                    <td class="px-6 py-4 text-slate-500">11/09/2026</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">En attente</span></td>
                    <td class="px-6 py-4 text-right"><button onclick="ACTION_JS" class="text-white bg-slate-800 hover:bg-slate-900 font-bold text-xs px-3 py-1.5 rounded-lg"><i class="las la-signature mr-1"></i>Signer</button></td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

<div class="bg-white rounded-3xl border border-slate-100 p-8 text-center space-y-3">
    <p class="text-[11px] font-black uppercase tracking-wider text-slate-400">Aperçu zone de signature</p>
    <div class="max-w-sm mx-auto h-32 bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl flex items-center justify-center text-slate-300">
        <i class="las la-pen-fancy text-3xl"></i>
    </div>
    <p class="text-xs text-slate-400">Signature capturée sur tablette / mobile, apposée automatiquement sur le rapport PDF généré.</p>
</div>
""".replace("ACTION_JS", ACTION_JS)

CONTENT_IOT = """
<div class="grid grid-cols-1 md:grid-cols-3 gap-5">
    <div class="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-3">
            <p class="text-[11px] font-black uppercase tracking-wider text-slate-400">Température moyenne</p>
            <i class="las la-thermometer-half text-blue-500 text-xl"></i>
        </div>
        <p class="text-3xl font-black text-slate-800">42.8 <span class="text-base font-bold text-slate-400">°C</span></p>
        <div class="w-full h-2 bg-slate-100 rounded-full mt-3 overflow-hidden"><div class="h-full bg-amber-500 rounded-full" style="width: 68%"></div></div>
        <p class="text-[11px] text-amber-600 font-bold mt-2">Seuil d'alerte : 45°C</p>
    </div>
    <div class="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-3">
            <p class="text-[11px] font-black uppercase tracking-wider text-slate-400">Vibration</p>
            <i class="las la-wave-square text-blue-500 text-xl"></i>
        </div>
        <p class="text-3xl font-black text-slate-800">2.1 <span class="text-base font-bold text-slate-400">mm/s</span></p>
        <div class="w-full h-2 bg-slate-100 rounded-full mt-3 overflow-hidden"><div class="h-full bg-emerald-500 rounded-full" style="width: 30%"></div></div>
        <p class="text-[11px] text-emerald-600 font-bold mt-2">Dans les normes</p>
    </div>
    <div class="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-3">
            <p class="text-[11px] font-black uppercase tracking-wider text-slate-400">Pression circuit</p>
            <i class="las la-tachometer-alt text-blue-500 text-xl"></i>
        </div>
        <p class="text-3xl font-black text-slate-800">6.4 <span class="text-base font-bold text-slate-400">bar</span></p>
        <div class="w-full h-2 bg-slate-100 rounded-full mt-3 overflow-hidden"><div class="h-full bg-rose-500 rounded-full" style="width: 91%"></div></div>
        <p class="text-[11px] text-rose-600 font-bold mt-2">Seuil critique approché</p>
    </div>
</div>

<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Alertes prédictives récentes</h2>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="px-6 py-3 font-bold">Capteur</th>
                    <th class="px-6 py-3 font-bold">Équipement</th>
                    <th class="px-6 py-3 font-bold">Niveau</th>
                    <th class="px-6 py-3 font-bold">Date</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Pression circuit</td>
                    <td class="px-6 py-4 text-slate-500">Compresseur CP-12</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-50 text-rose-600 border border-rose-100">Critique</span></td>
                    <td class="px-6 py-4 text-slate-500">Aujourd'hui, 09:14</td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Température</td>
                    <td class="px-6 py-4 text-slate-500">Groupe froid GF-9</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-100">Attention</span></td>
                    <td class="px-6 py-4 text-slate-500">Hier, 22:47</td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Vibration</td>
                    <td class="px-6 py-4 text-slate-500">Pont élévateur PE-2</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Résolue</span></td>
                    <td class="px-6 py-4 text-slate-500">07/09/2026</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
"""

CONTENT_STOCK = """
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Références en stock</p>
        <p class="text-2xl font-black text-slate-800">246</p>
    </div>
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Sous le seuil d'alerte</p>
        <p class="text-2xl font-black text-rose-600">4</p>
    </div>
    <div class="bg-white rounded-2xl border border-slate-100 p-5">
        <p class="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1">Valeur totale du stock</p>
        <p class="text-2xl font-black text-slate-800">18 420 €</p>
    </div>
</div>

<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Inventaire des pièces détachées</h2>
        <button onclick="ACTION_JS" class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold px-4 py-2 rounded-xl text-xs transition">
            <i class="las la-plus"></i> Nouvelle pièce
        </button>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="px-6 py-3 font-bold">Pièce</th>
                    <th class="px-6 py-3 font-bold">Référence</th>
                    <th class="px-6 py-3 font-bold">Quantité</th>
                    <th class="px-6 py-3 font-bold">Seuil d'alerte</th>
                    <th class="px-6 py-3 font-bold">Statut</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Filtre à air CP-12</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">FLT-AIR-012</td>
                    <td class="px-6 py-4 text-slate-500">34</td>
                    <td class="px-6 py-4 text-slate-500">10</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">OK</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Courroie FX-3</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">CRR-FX3-004</td>
                    <td class="px-6 py-4 text-slate-500">3</td>
                    <td class="px-6 py-4 text-slate-500">5</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-50 text-rose-600 border border-rose-100">Stock bas</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Joint hydraulique PE-2</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">JNT-PE2-021</td>
                    <td class="px-6 py-4 text-slate-500">2</td>
                    <td class="px-6 py-4 text-slate-500">5</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-50 text-rose-600 border border-rose-100">Stock bas</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Capteur température GF-9</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">CPT-TMP-009</td>
                    <td class="px-6 py-4 text-slate-500">17</td>
                    <td class="px-6 py-4 text-slate-500">8</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">OK</span></td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700">Kit d'étanchéité chaudière</td>
                    <td class="px-6 py-4 text-slate-500 font-mono">KIT-CHD-007</td>
                    <td class="px-6 py-4 text-slate-500">9</td>
                    <td class="px-6 py-4 text-slate-500">6</td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">OK</span></td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
""".replace("ACTION_JS", ACTION_JS)

CONTENT_MAP = """
<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Carte des sites clients</h2>
    </div>
    <div class="relative h-80 bg-slate-100" style="background-image: linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(90deg, #e2e8f0 1px, transparent 1px); background-size: 32px 32px;">
        <div class="absolute" style="top: 30%; left: 22%;">
            <div class="h-8 w-8 -mt-8 -ml-4 bg-blue-600 text-white rounded-full rounded-bl-none flex items-center justify-center shadow-lg rotate-45"><i class="las la-map-marker-alt text-lg -rotate-45"></i></div>
        </div>
        <div class="absolute" style="top: 55%; left: 48%;">
            <div class="h-8 w-8 -mt-8 -ml-4 bg-blue-600 text-white rounded-full rounded-bl-none flex items-center justify-center shadow-lg rotate-45"><i class="las la-map-marker-alt text-lg -rotate-45"></i></div>
        </div>
        <div class="absolute" style="top: 40%; left: 68%;">
            <div class="h-8 w-8 -mt-8 -ml-4 bg-rose-500 text-white rounded-full rounded-bl-none flex items-center justify-center shadow-lg rotate-45"><i class="las la-map-marker-alt text-lg -rotate-45"></i></div>
        </div>
        <div class="absolute" style="top: 68%; left: 30%;">
            <div class="h-8 w-8 -mt-8 -ml-4 bg-blue-600 text-white rounded-full rounded-bl-none flex items-center justify-center shadow-lg rotate-45"><i class="las la-map-marker-alt text-lg -rotate-45"></i></div>
        </div>
        <div class="absolute bottom-3 right-3 bg-white/90 backdrop-blur px-3 py-1.5 rounded-full text-[10px] font-bold text-slate-500 shadow-sm">Fond de carte simplifié — mode démonstration</div>
    </div>
</div>

<div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <h2 class="font-bold text-slate-800 text-sm">Sites géolocalisés</h2>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="px-6 py-3 font-bold">Site</th>
                    <th class="px-6 py-3 font-bold">Client</th>
                    <th class="px-6 py-3 font-bold">Adresse</th>
                    <th class="px-6 py-3 font-bold">Équipements</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700"><i class="las la-map-marker-alt text-blue-500 mr-1"></i>Site Nord</td>
                    <td class="px-6 py-4 text-slate-500">Atelier Dupont SA</td>
                    <td class="px-6 py-4 text-slate-500">12 rue des Forges, Liège</td>
                    <td class="px-6 py-4 text-slate-500">3</td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700"><i class="las la-map-marker-alt text-blue-500 mr-1"></i>Site Centre</td>
                    <td class="px-6 py-4 text-slate-500">Clinique Vetalis</td>
                    <td class="px-6 py-4 text-slate-500">45 avenue de la Santé, Namur</td>
                    <td class="px-6 py-4 text-slate-500">5</td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700"><i class="las la-map-marker-alt text-rose-500 mr-1"></i>Site Est</td>
                    <td class="px-6 py-4 text-slate-500">Hôtel Bellevue</td>
                    <td class="px-6 py-4 text-slate-500">3 place du Marché, Verviers</td>
                    <td class="px-6 py-4 text-slate-500">2 (1 alerte active)</td>
                </tr>
                <tr class="hover:bg-slate-50/50 transition">
                    <td class="px-6 py-4 font-semibold text-slate-700"><i class="las la-map-marker-alt text-blue-500 mr-1"></i>Site Sud</td>
                    <td class="px-6 py-4 text-slate-500">Garage Meunier</td>
                    <td class="px-6 py-4 text-slate-500">78 chaussée de Charleroi, Namur</td>
                    <td class="px-6 py-4 text-slate-500">4</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
"""

# ---------------------------------------------------------------------------
# Configuration des 7 modules premium à générer.
# ---------------------------------------------------------------------------
modules_config = [
    {
        "slug": "contrats-de-maintenance",
        "name": "Contrats de Maintenance",
        "label": "Contrats de Maintenance",
        "icon": "la-file-contract",
        "desc": "Gestion et automatisation des contrats de maintenance récurrents.",
        "content": CONTENT_CONTRACTS,
    },
    {
        "slug": "gestion-de-la-flotte-vehicules",
        "name": "Gestion de la Flotte Véhicules",
        "label": "Flotte Véhicules",
        "icon": "la-car",
        "desc": "Suivi et attribution de la flotte de véhicules de maintenance.",
        "content": CONTENT_FLEET,
    },
    {
        "slug": "hrm-absences-redistribution-de-charge",
        "name": "HRM - Absences & Redistribution de Charge",
        "label": "Planning & RH",
        "icon": "la-users-cog",
        "desc": "Gestion des absences, congés et répartition de la charge.",
        "content": CONTENT_HRM,
    },
    {
        "slug": "signature-electronique-rapports-pdf",
        "name": "Signature Électronique & Rapports PDF",
        "label": "Signature & Rapports",
        "icon": "la-signature",
        "desc": "Signature électronique des bons d'intervention et rapports PDF.",
        "content": CONTENT_SIGNATURE,
    },
    {
        "slug": "iot-alertes-predictives",
        "name": "IoT & Alertes Prédictives",
        "label": "IoT & Alertes",
        "icon": "la-broadcast-tower",
        "desc": "Surveillance par capteurs connectés et génération d'alertes.",
        "content": CONTENT_IOT,
    },
    {
        "slug": "stock-pieces-detachees",
        "name": "Stock & Pièces Détachées",
        "label": "Stock & Pièces",
        "icon": "la-boxes",
        "desc": "Suivi de l'inventaire des pièces détachées et alertes.",
        "content": CONTENT_STOCK,
    },
    {
        "slug": "localisation-des-sites",
        "name": "Localisation des sites",
        "label": "Localisation des Sites",
        "icon": "la-map-marked-alt",
        "desc": "Cartographie interactive et géolocalisation des sites.",
        "content": CONTENT_MAP,
    },
]


def write_package_tree(config, dest_dir, version=PACKAGE_VERSION):
    """
    Écrit dans `dest_dir` l'arborescence d'un module de démonstration (pyproject.toml + paquet Python
    avec ses gabarits) et retourne le nom du paquet. Toute valeur insérée dans du code Python passe par
    repr() pour rester valide même avec des apostrophes ou des guillemets.
    """
    slug = config["slug"]
    package_name = slug.replace('-', '_')
    app_dir = os.path.join(dest_dir, package_name)
    os.makedirs(app_dir, exist_ok=True)

    pyproject_content = f"""[project]
name = "smartops-plugin-{slug}"
version = "{version}"
dependencies = ["pluggy>=1.0.0"]

[project.entry-points."smartops.plugins"]
{package_name} = "{package_name}.hookimpls:plugin_implementation"

[build-system]
requires = ["setuptools>=64.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.package-data]
{package_name} = ["templates/**/*.html"]
"""
    with open(os.path.join(dest_dir, "pyproject.toml"), "w", encoding="utf-8") as f:
        f.write(pyproject_content)

    with open(os.path.join(app_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write("")

    hookimpls_content = f"""import pluggy
hookimpl = pluggy.HookimplMarker("smartops")

class PlaceholderPlugin:
    @hookimpl
    def register_menu_items(self):
        return [{{
            "label": {config["label"]!r},
            "url": "/app/{package_name}/",
            "icon": {config["icon"]!r}
        }}]

plugin_implementation = PlaceholderPlugin()
"""
    with open(os.path.join(app_dir, "hookimpls.py"), "w", encoding="utf-8") as f:
        f.write(hookimpls_content)

    urls_content = """from django.urls import path
from . import views
urlpatterns = [
    path('', views.index_view, name='index'),
]
"""
    with open(os.path.join(app_dir, "urls.py"), "w", encoding="utf-8") as f:
        f.write(urls_content)

    views_content = f"""from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index_view(request):
    return render(request, {package_name + '/index.html'!r}, {{
        'page_title': {config["name"]!r},
        'description': {config["desc"]!r},
    }})
"""
    with open(os.path.join(app_dir, "views.py"), "w", encoding="utf-8") as f:
        f.write(views_content)

    templates_dir = os.path.join(app_dir, "templates", package_name)
    os.makedirs(templates_dir, exist_ok=True)
    html_content = (
        BASE_TEMPLATE
        .replace("__NAME__", config["name"])
        .replace("__DESC__", config["desc"])
        .replace("__ICON__", config["icon"])
        .replace("__CONTENT__", config["content"])
    )
    with open(os.path.join(templates_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    return package_name


def run():
    print("Début de la génération des packages de plugins placeholders...")

    core_version = CoreVersion.objects.first()
    if not core_version:
        print("Création de la version Core 1.0 par défaut...")
        core_version = CoreVersion.objects.create(version="1.0", is_active=True)

    packages_dir = os.path.join(settings.MEDIA_ROOT, "modules", "packages")
    os.makedirs(packages_dir, exist_ok=True)

    for config in modules_config:
        slug = config["slug"]
        module = Module.objects.filter(slug_fr=slug).first()
        if not module:
            print(f"Erreur : Le module '{slug}' n'existe pas en base de données.")
            continue

        package_name = slug.replace('-', '_')
        print(f"Génération du package pour : {module.name} ({package_name})...")

        with tempfile.TemporaryDirectory() as temp_dir:
            write_package_tree(config, temp_dir)
            app_dir = os.path.join(temp_dir, package_name)

            archive_filename = f"{package_name}_placeholder.tar.gz"
            archive_path = os.path.join(packages_dir, archive_filename)

            if os.path.exists(archive_path):
                os.remove(archive_path)

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(os.path.join(temp_dir, "pyproject.toml"), arcname="pyproject.toml")
                tar.add(app_dir, arcname=package_name)

            print(f"Archive créée : {archive_filename}")

            version_rel_path = f"modules/packages/{archive_filename}"

            ModuleVersion.objects.filter(module=module).delete()

            ModuleVersion.objects.create(
                module=module,
                version_number=PACKAGE_VERSION,
                release_date=date.today(),
                min_core_version=core_version,
                changelog="Correction des modules de démonstration : textes échappés et gabarits inclus dans le paquet.",
                file=version_rel_path
            )
            print(f"Base de données mise à jour : {module.name} v{PACKAGE_VERSION} -> {version_rel_path}")

    print("Génération de tous les packages placeholders complétée avec succès !")


if __name__ == '__main__':
    run()

"""
Fichier : filters.py
Projet : Marketplace SMARTOPS
Application : backoffice
Description : Moteur de filtres par critères pour les listes du backoffice.

Chaque liste déclare ses critères en quelques lignes, puis applique le moteur avant la pagination :

    filters = FilterSet(request, [
        Search('q', _("Rechercher"), fields=['name_fr', 'name_en']),
        Choice('status', _("Statut"), field='status', choices=Order.STATUS_CHOICES),
        DateRange('created', _("Date de création"), field='created_at', advanced=True),
    ])
    items = paginate(request, filters.apply(queryset))

et affiche la barre de filtres avec `{% include "backoffice/_filters.html" %}` (variable `filters`).
Les critères lisent les paramètres GET ; une valeur absente ou invalide est simplement ignorée.
"""

import datetime
from decimal import Decimal, InvalidOperation
from functools import reduce
from operator import and_, or_
from urllib.parse import urlencode

from django.db.models import Q
from django.utils.translation import gettext as _

# Paramètres de pagination : jamais considérés comme des critères de filtre.
PAGINATION_PARAMS = ('page', 'per_page')


def _resolve_field(model, path):
    """Retourne le champ de modèle désigné par un chemin `relation__champ` (None si introuvable)."""
    field = None
    for part in path.split('__'):
        if model is None:
            return None
        try:
            field = model._meta.get_field(part)
        except Exception:
            return None
        model = field.related_model if field.is_relation else None
    return field


class Criterion:
    """Critère de filtre : lit ses paramètres GET, applique un filtre et sait se décrire."""

    kind = 'text'

    def __init__(self, name, label, advanced=False):
        self.name = name
        self.label = label
        self.advanced = advanced

    @property
    def params(self):
        return [self.name]

    def parse(self, data):
        """Retourne la valeur valide lue dans `data` (QueryDict) ou None."""
        raise NotImplementedError

    def apply(self, queryset, value):
        raise NotImplementedError

    def describe(self, value):
        """Texte affiché dans l'étiquette du critère actif."""
        return str(value)

    def context(self, value):
        """Données nécessaires au gabarit pour afficher le champ."""
        return {'name': self.name, 'label': self.label, 'kind': self.kind, 'advanced': self.advanced, 'value': value or ''}


class Search(Criterion):
    """Recherche texte : chaque mot doit se trouver dans au moins un des champs (insensible à la casse)."""

    kind = 'text'

    def __init__(self, name, label, fields, id_field=None, advanced=False):
        super().__init__(name, label, advanced)
        self.fields = fields
        self.id_field = id_field

    def parse(self, data):
        value = ' '.join((data.get(self.name) or '').split())
        return value[:100] or None

    def apply(self, queryset, value):
        for term in value.split(' '):
            options = [Q(**{f'{field}__icontains': term}) for field in self.fields]
            digits = term.lstrip('#')
            if self.id_field and digits.isdigit():
                options.append(Q(**{self.id_field: int(digits)}))
            queryset = queryset.filter(reduce(or_, options))
        return queryset


class Choice(Criterion):
    """Liste de choix fixes : le champ doit valoir la valeur choisie."""

    kind = 'select'

    def __init__(self, name, label, choices, field=None, apply=None, advanced=False):
        super().__init__(name, label, advanced)
        self.choices = [(str(value), str(text)) for value, text in choices]
        self.field = field
        self.custom_apply = apply

    def parse(self, data):
        value = data.get(self.name)
        return value if value in dict(self.choices) else None

    def apply(self, queryset, value):
        if self.custom_apply:
            return self.custom_apply(queryset, value)
        return queryset.filter(**{self.field: value})

    def describe(self, value):
        return dict(self.choices).get(value, value)

    def context(self, value):
        data = super().context(value)
        data['options'] = self.choices
        return data


class Bool(Choice):
    """Oui / non sur un champ booléen (ou sur deux filtres personnalisés)."""

    def __init__(self, name, label, field=None, true_label=None, false_label=None, apply=None, advanced=False):
        choices = [('1', true_label or _("Oui")), ('0', false_label or _("Non"))]
        super().__init__(name, label, choices, field=field, apply=apply, advanced=advanced)

    def apply(self, queryset, value):
        if self.custom_apply:
            return self.custom_apply(queryset, value == '1')
        return queryset.filter(**{self.field: value == '1'})


class ModelChoice(Choice):
    """Choix parmi des objets (catégorie, module…) : le champ relationnel doit valoir l'objet choisi."""

    def __init__(self, name, label, queryset, field=None, apply=None, text=str, advanced=False):
        super().__init__(name, label, [(obj.pk, text(obj)) for obj in queryset], field=field, apply=apply, advanced=advanced)

    def apply(self, queryset, value):
        if self.custom_apply:
            return self.custom_apply(queryset, int(value))
        return queryset.filter(**{self.field: int(value)})


class DateRange(Criterion):
    """Période « du … au … » (bornes incluses) sur un champ date ou date-heure."""

    kind = 'date_range'

    def __init__(self, name, label, field, advanced=True):
        super().__init__(name, label, advanced)
        self.field = field

    @property
    def params(self):
        return [f'{self.name}_from', f'{self.name}_to']

    @staticmethod
    def _date(raw):
        try:
            return datetime.date.fromisoformat(raw) if raw else None
        except ValueError:
            return None

    def parse(self, data):
        start, end = self._date(data.get(f'{self.name}_from')), self._date(data.get(f'{self.name}_to'))
        if start and end and start > end:
            start, end = end, start
        return (start, end) if (start or end) else None

    def apply(self, queryset, value):
        start, end = value
        field = _resolve_field(queryset.model, self.field)
        suffix = '__date' if field is not None and field.get_internal_type() == 'DateTimeField' else ''
        if start:
            queryset = queryset.filter(**{f'{self.field}{suffix}__gte': start})
        if end:
            queryset = queryset.filter(**{f'{self.field}{suffix}__lte': end})
        return queryset

    def describe(self, value):
        start, end = value
        if start and end:
            return f'{start.isoformat()} → {end.isoformat()}'
        return f'≥ {start.isoformat()}' if start else f'≤ {end.isoformat()}'

    def context(self, value):
        data = super().context(None)
        start, end = value if value else (None, None)
        data.update({'from_name': f'{self.name}_from', 'to_name': f'{self.name}_to',
                     'from_value': start.isoformat() if start else '', 'to_value': end.isoformat() if end else ''})
        return data


class NumberRange(Criterion):
    """Fourchette de nombres « min … max » (bornes incluses)."""

    kind = 'number_range'

    def __init__(self, name, label, field, advanced=True):
        super().__init__(name, label, advanced)
        self.field = field

    @property
    def params(self):
        return [f'{self.name}_min', f'{self.name}_max']

    @staticmethod
    def _number(raw):
        try:
            return Decimal(raw) if raw not in (None, '') else None
        except (InvalidOperation, ValueError):
            return None

    def parse(self, data):
        low, high = self._number(data.get(f'{self.name}_min')), self._number(data.get(f'{self.name}_max'))
        if low is not None and high is not None and low > high:
            low, high = high, low
        return (low, high) if (low is not None or high is not None) else None

    def apply(self, queryset, value):
        low, high = value
        if low is not None:
            queryset = queryset.filter(**{f'{self.field}__gte': low})
        if high is not None:
            queryset = queryset.filter(**{f'{self.field}__lte': high})
        return queryset

    def describe(self, value):
        low, high = value
        if low is not None and high is not None:
            return f'{low.normalize():f} → {high.normalize():f}'
        return f'≥ {low.normalize():f}' if low is not None else f'≤ {high.normalize():f}'

    def context(self, value):
        data = super().context(None)
        low, high = value if value else (None, None)
        data.update({'min_name': f'{self.name}_min', 'max_name': f'{self.name}_max',
                     'min_value': f'{low.normalize():f}' if low is not None else '',
                     'max_value': f'{high.normalize():f}' if high is not None else ''})
        return data


class FilterSet:
    """Ensemble de critères appliqués à une liste à partir des paramètres GET de la requête."""

    def __init__(self, request, criteria):
        self.request = request
        self.criteria = list(criteria)
        self.values = {c.name: c.parse(request.GET) for c in self.criteria}

    def apply(self, queryset):
        for criterion in self.criteria:
            value = self.values[criterion.name]
            if value is not None:
                queryset = criterion.apply(queryset, value)
        return queryset

    def _query_without(self, params):
        """Chaîne de requête de l'URL courante sans certains paramètres (et sans la page)."""
        remaining = [(k, v) for k in self.request.GET for v in self.request.GET.getlist(k)
                     if k not in params and k != 'page']
        return urlencode(remaining)

    def _url(self, query):
        return f'?{query}' if query else self.request.path

    @property
    def active(self):
        """Critères actifs : étiquette, valeur et adresse qui retire ce critère."""
        return [
            {'label': c.label, 'text': c.describe(self.values[c.name]),
             'remove_url': self._url(self._query_without(c.params))}
            for c in self.criteria if self.values[c.name] is not None
        ]

    @property
    def is_active(self):
        return any(value is not None for value in self.values.values())

    @property
    def reset_url(self):
        keep = [(k, v) for k in self.request.GET for v in self.request.GET.getlist(k) if k == 'per_page']
        return self._url(urlencode(keep))

    @property
    def per_page(self):
        return self.request.GET.get('per_page', '')

    @property
    def fields(self):
        return [c.context(self.values[c.name]) for c in self.criteria if not c.advanced]

    @property
    def advanced_fields(self):
        return [c.context(self.values[c.name]) for c in self.criteria if c.advanced]

    @property
    def advanced_open(self):
        return any(self.values[c.name] is not None for c in self.criteria if c.advanced)

"""
Tests du moteur de filtres du backoffice (backoffice/filters.py) et de son utilisation sur les listes.
"""

import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import Client as HttpClient, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from backoffice.filters import Bool, Choice, DateRange, FilterSet, ModelChoice, NumberRange, Search
from catalog.models import Category, Module
from payments.models import Order, OrderItem

User = get_user_model()
factory = RequestFactory()


def request_with(**params):
    return factory.get('/fr/backoffice/modules/', params)


class EngineFixtureMixin:
    """Deux catégories, quatre modules de prix et de statuts différents, quelques ventes."""

    def make_fixtures(self):
        self.cat_a = Category.objects.create(name='Analytics', slug='analytics')
        self.cat_b = Category.objects.create(name='IoT', slug='iot')
        make = lambda name, slug, cat, price, active=True, support=None: Module.objects.create(
            name=name, slug=slug, category=cat, price=Decimal(price), is_active=active,
            support_annual_price=Decimal(support) if support else None)
        self.bi = make('Tableau BI', 'tableau-bi', self.cat_a, '200.00', support='40.00')
        self.stock = make('Stock Pièces', 'stock-pieces', self.cat_a, '50.00', active=False)
        self.flotte = make('Flotte Véhicules', 'flotte-vehicules', self.cat_b, '120.50')
        self.capteurs = make('Capteurs IoT', 'capteurs-iot', self.cat_b, '300.00', support='90.00')


class SearchCriterionTests(EngineFixtureMixin, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.criterion = Search('q', 'Rechercher', fields=['name_fr', 'slug_fr'])

    def names(self, **params):
        fs = FilterSet(request_with(**params), [self.criterion])
        return sorted(m.name for m in fs.apply(Module.objects.all()))

    def test_case_insensitive_partial_match(self):
        self.assertEqual(self.names(q='stock'), ['Stock Pièces'])
        self.assertEqual(self.names(q='FLOTTE'), ['Flotte Véhicules'])

    def test_all_words_must_match_in_any_field(self):
        self.assertEqual(self.names(q='tableau bi'), ['Tableau BI'])
        self.assertEqual(self.names(q='stock flotte'), [])          # ET entre les mots
        self.assertEqual(self.names(q='iot capteurs'), ['Capteurs IoT'])

    def test_search_reaches_every_configured_field(self):
        self.assertEqual(self.names(q='vehicules'), ['Flotte Véhicules'])   # via le slug

    def test_empty_or_blank_value_is_ignored(self):
        for blank in ('', '   '):
            self.assertEqual(len(self.names(q=blank)), 4)

    def test_value_is_trimmed_and_capped(self):
        criterion = self.criterion
        self.assertEqual(criterion.parse({'q': '  a   b  '}), 'a b')
        self.assertEqual(len(criterion.parse({'q': 'x' * 500})), 100)

    def test_numeric_term_can_match_the_id(self):
        criterion = Search('q', 'Rechercher', fields=['name_fr'], id_field='id')
        fs = FilterSet(request_with(q=f'#{self.bi.pk}'), [criterion])
        self.assertEqual([m.pk for m in fs.apply(Module.objects.all())], [self.bi.pk])

    def test_sql_wildcards_and_quotes_are_harmless(self):
        for hostile in ("' OR 1=1 --", '%', '_', '"><script>alert(1)</script>'):
            self.assertEqual(self.names(q=hostile), [])


class ChoiceBoolModelChoiceTests(EngineFixtureMixin, TestCase):
    def setUp(self):
        self.make_fixtures()

    def apply(self, criterion, **params):
        return sorted(m.name for m in FilterSet(request_with(**params), [criterion]).apply(Module.objects.all()))

    def test_bool_true_false_and_invalid(self):
        criterion = Bool('active', 'Actif', field='is_active')
        self.assertEqual(self.apply(criterion, active='0'), ['Stock Pièces'])
        self.assertEqual(len(self.apply(criterion, active='1')), 3)
        self.assertEqual(len(self.apply(criterion, active='peut-être')), 4)      # valeur invalide ignorée

    def test_bool_with_custom_apply(self):
        criterion = Bool('support', 'Support', apply=lambda qs, yes: qs.filter(support_annual_price__isnull=not yes))
        self.assertEqual(self.apply(criterion, support='1'), ['Capteurs IoT', 'Tableau BI'])
        self.assertEqual(self.apply(criterion, support='0'), ['Flotte Véhicules', 'Stock Pièces'])

    def test_choice_accepts_only_declared_values(self):
        criterion = Choice('state', 'État', [('on', 'Oui'), ('off', 'Non')],
                           apply=lambda qs, v: qs.filter(is_active=(v == 'on')))
        self.assertEqual(self.apply(criterion, state='off'), ['Stock Pièces'])
        self.assertEqual(len(self.apply(criterion, state='hack')), 4)

    def test_model_choice_by_id_and_unknown_id(self):
        criterion = ModelChoice('category', 'Catégorie', Category.objects.all(), field='category')
        self.assertEqual(self.apply(criterion, category=str(self.cat_b.pk)), ['Capteurs IoT', 'Flotte Véhicules'])
        self.assertEqual(len(self.apply(criterion, category='999999')), 4)
        self.assertEqual(len(self.apply(criterion, category='abc')), 4)


class RangeCriteriaTests(EngineFixtureMixin, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.buyer = User.objects.create_user('buyer', 'buyer@example.org', 'x')
        self.orders = {}
        for label, moment in (('debut', datetime.datetime(2026, 3, 1, 0, 0)), ('fin', datetime.datetime(2026, 3, 10, 23, 59)),
                              ('apres', datetime.datetime(2026, 3, 11, 0, 1))):
            order = Order.objects.create(user=self.buyer, status='completed', total_amount=Decimal('10.00'))
            Order.objects.filter(pk=order.pk).update(created_at=timezone.make_aware(moment))
            self.orders[label] = order.pk

    def prices(self, **params):
        fs = FilterSet(request_with(**params), [NumberRange('price', 'Prix', field='price')])
        return sorted(m.name for m in fs.apply(Module.objects.all()))

    def order_ids(self, **params):
        fs = FilterSet(request_with(**params), [DateRange('created', 'Date', field='created_at')])
        return sorted(fs.apply(Order.objects.all()).values_list('pk', flat=True))

    def test_number_range_bounds_are_inclusive(self):
        self.assertEqual(self.prices(price_min='50', price_max='120.50'), ['Flotte Véhicules', 'Stock Pièces'])
        self.assertEqual(self.prices(price_min='300'), ['Capteurs IoT'])
        self.assertEqual(self.prices(price_max='50'), ['Stock Pièces'])

    def test_number_range_swapped_and_invalid_values(self):
        self.assertEqual(self.prices(price_min='300', price_max='200'), ['Capteurs IoT', 'Tableau BI'])
        self.assertEqual(len(self.prices(price_min='abc', price_max='')), 4)

    def test_date_range_includes_the_whole_last_day(self):
        got = self.order_ids(created_from='2026-03-01', created_to='2026-03-10')
        self.assertEqual(got, sorted([self.orders['debut'], self.orders['fin']]))   # 23:59 du dernier jour compris

    def test_date_range_open_ended_swapped_and_invalid(self):
        self.assertEqual(self.order_ids(created_from='2026-03-11'), [self.orders['apres']])
        self.assertEqual(self.order_ids(created_to='2026-03-01'), [self.orders['debut']])
        self.assertEqual(len(self.order_ids(created_from='2026-03-10', created_to='2026-03-01')), 2)   # bornes inversées
        self.assertEqual(len(self.order_ids(created_from='pas-une-date', created_to='2026-13-45')), 3)

    def test_date_range_on_a_related_datetime_field(self):
        item_module = self.bi
        OrderItem.objects.create(order=Order.objects.get(pk=self.orders['fin']), module=item_module, price_at_purchase=Decimal('10'))
        criterion = DateRange('sold', 'Vente', field='order__created_at')
        qs = FilterSet(request_with(sold_from='2026-03-10', sold_to='2026-03-10'), [criterion]).apply(OrderItem.objects.all())
        self.assertEqual(qs.count(), 1)


class FilterSetBehaviourTests(EngineFixtureMixin, TestCase):
    def setUp(self):
        self.make_fixtures()

    def build(self, **params):
        return FilterSet(request_with(**params), [
            Search('q', 'Rechercher', fields=['name_fr']),
            ModelChoice('category', 'Catégorie', Category.objects.all(), field='category'),
            Bool('active', 'Actif', field='is_active'),
            NumberRange('price', 'Prix', field='price'),
            DateRange('created', 'Création', field='created_at'),
        ])

    def test_criteria_combine_with_and(self):
        fs = self.build(category=str(self.cat_a.pk), active='1', price_min='100')
        self.assertEqual([m.name for m in fs.apply(Module.objects.all())], ['Tableau BI'])

    def test_no_parameter_returns_everything_and_is_inactive(self):
        fs = self.build()
        self.assertEqual(fs.apply(Module.objects.all()).count(), 4)
        self.assertFalse(fs.is_active)
        self.assertEqual(fs.active, [])

    def test_active_chips_describe_each_criterion_and_remove_only_their_own_params(self):
        fs = self.build(q='tab', price_min='10', price_max='99', page='3', per_page='50')
        chips = {c['label']: c for c in fs.active}
        self.assertEqual(set(chips), {'Rechercher', 'Prix'})
        self.assertEqual(chips['Prix']['text'], '10 → 99')
        remove_price = chips['Prix']['remove_url']
        self.assertIn('q=tab', remove_price)
        self.assertIn('per_page=50', remove_price)
        self.assertNotIn('price_min', remove_price)
        self.assertNotIn('page=3', remove_price)                     # on revient à la première page
        self.assertEqual(chips['Rechercher']['remove_url'].count('price_min'), 1)

    def test_removing_the_last_criterion_leaves_the_bare_path(self):
        fs = self.build(q='tab')
        self.assertEqual(fs.active[0]['remove_url'], '/fr/backoffice/modules/')

    def test_reset_url_keeps_only_the_page_size(self):
        fs = self.build(q='tab', category='1', per_page='100', page='2')
        self.assertEqual(fs.reset_url, '?per_page=100')
        self.assertEqual(self.build(q='x').reset_url, '/fr/backoffice/modules/')

    def test_advanced_fields_are_separated_and_open_only_when_used(self):
        fs = self.build()
        self.assertEqual([f['name'] for f in fs.fields], ['q', 'category', 'active'])
        self.assertEqual([f['name'] for f in fs.advanced_fields], ['price', 'created'])
        self.assertFalse(fs.advanced_open)
        self.assertTrue(self.build(price_min='5').advanced_open)

    def test_invalid_values_never_raise(self):
        fs = self.build(q='\x00', category='x', active='zz', price_min='1e999999', created_from='0000-00-00')
        fs.apply(Module.objects.all()).count()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FilterBarRenderingTests(EngineFixtureMixin, TestCase):
    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        self.make_fixtures()

    def render(self, lang='fr', **params):
        request = request_with(**params)
        filters = FilterSet(request, [
            Search('q', 'Rechercher', fields=['name_fr']),
            ModelChoice('category', 'Catégorie', Category.objects.all(), field='category'),
            NumberRange('price', 'Prix', field='price'),
        ])
        with translation.override(lang):
            return render_to_string('backoffice/_filters.html', {'filters': filters, 'page': None}, request=request)

    def test_fields_show_current_values_and_options(self):
        html = self.render(q='stock', category=str(self.cat_b.pk), price_min='10')
        self.assertIn('value="stock"', html)
        self.assertIn(f'<option value="{self.cat_b.pk}" selected>IoT</option>', html)
        self.assertIn('name="price_min" value="10"', html)
        self.assertIn('<details open>', html)                # critère avancé actif => ouvert

    def test_typed_text_is_escaped(self):
        html = self.render(q='"><script>alert(1)</script>')
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_page_size_is_kept_in_the_form(self):
        self.assertIn('name="per_page" value="50"', self.render(per_page='50'))
        self.assertNotIn('name="per_page"', self.render())

    def test_reset_button_only_when_a_filter_is_active(self):
        self.assertNotIn('Réinitialiser', self.render())
        self.assertIn('Réinitialiser', self.render(q='x'))

    def test_interface_is_translated(self):
        for lang, expected in (('fr', ('Filtrer', 'Plus de critères', 'Tous')),
                               ('en', ('Filter', 'More criteria', 'All')),
                               ('nl', ('Filteren', 'Meer criteria', 'Alle'))):
            html = self.render(lang, q='x')
            for text in expected:
                self.assertIn(text, html, f'{text} ({lang})')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ModuleListFiltersTests(EngineFixtureMixin, TestCase):
    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        self.make_fixtures()
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.http = HttpClient()
        self.http.login(username='admin_boss', password='AdminPassword123!')
        self.url = reverse('backoffice:module_list')
        buyer = User.objects.create_user('buyer', 'b@example.org', 'x')
        order = Order.objects.create(user=buyer, status='completed', total_amount=Decimal('200'))
        OrderItem.objects.create(order=order, module=self.bi, price_at_purchase=Decimal('200'))

    def names(self, **params):
        response = self.http.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return sorted(m.name for m in response.context['modules'])

    def test_each_criterion(self):
        self.assertEqual(self.names(q='iot'), ['Capteurs IoT'])
        self.assertEqual(self.names(category=str(self.cat_a.pk)), ['Stock Pièces', 'Tableau BI'])
        self.assertEqual(self.names(active='0'), ['Stock Pièces'])
        self.assertEqual(self.names(sales='yes'), ['Tableau BI'])
        self.assertEqual(len(self.names(sales='no')), 3)
        self.assertEqual(self.names(support='1'), ['Capteurs IoT', 'Tableau BI'])
        self.assertEqual(self.names(price_min='100', price_max='250'), ['Flotte Véhicules', 'Tableau BI'])
        self.assertEqual(len(self.names(created_from=datetime.date.today().isoformat())), 4)
        self.assertEqual(self.names(created_to='2000-01-01'), [])

    def test_criteria_combine(self):
        self.assertEqual(self.names(category=str(self.cat_b.pk), support='1', price_min='250'), ['Capteurs IoT'])

    def test_garbage_parameters_do_not_break_the_page(self):
        self.assertEqual(len(self.names(category='x', active='zz', price_min='??', created_from='nope', sales='?')), 4)

    def test_results_counter_and_chips_are_displayed(self):
        html = self.http.get(self.url, {'active': '0', 'q': 'stock'}).content.decode()
        self.assertIn('1 résultat(s)', html)
        self.assertIn('Filtres actifs', html)
        self.assertIn('Actif : Non', html)

    def test_filters_survive_pagination_and_page_size_links(self):
        for i in range(30):
            Module.objects.create(name=f'Extra {i}', slug=f'extra-{i}', category=self.cat_a, price=Decimal('10'))
        response = self.http.get(self.url, {'q': 'extra', 'per_page': '10'})
        self.assertEqual(response.context['page'].paginator.count, 30)
        html = response.content.decode()
        self.assertRegex(html, r'href="\?[^"]*q=extra[^"]*page=2')
        self.assertRegex(html, r'href="\?[^"]*q=extra[^"]*per_page=50')

    def test_filter_bar_is_present_in_three_languages(self):
        for lang, expected in (('fr', 'Filtrer'), ('en', 'Filter'), ('nl', 'Filteren')):
            with translation.override(lang):
                url = reverse('backoffice:module_list')
            self.assertContains(self.http.get(url), expected)

    def test_requires_admin(self):
        self.assertNotEqual(HttpClient().get(self.url, {'q': 'x'}).status_code, 200)

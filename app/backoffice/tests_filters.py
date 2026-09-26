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


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CatalogListsFiltersTests(EngineFixtureMixin, TestCase):
    """Filtres des packs, catégories et versions du Core (issue #26)."""

    def setUp(self):
        from catalog.models import CoreVersion, ModuleBundle
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        self.make_fixtures()
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.http = HttpClient()
        self.http.login(username='admin_boss', password='AdminPassword123!')
        now = timezone.now()
        day = datetime.timedelta(days=1)
        mk = lambda name, slug, **kw: ModuleBundle.objects.create(name=name, slug=slug, short_description='x', description='x', **kw)
        self.pack_current = mk('Pack Actuel', 'pack-actuel', start_date=now - 5 * day, end_date=now + 5 * day)
        self.pack_open = mk('Pack Ouvert', 'pack-ouvert')
        self.pack_upcoming = mk('Pack Futur', 'pack-futur', start_date=now + 3 * day)
        self.pack_expired = mk('Pack Périmé', 'pack-perime', start_date=now - 9 * day, end_date=now - 2 * day, is_active=False,
                               discount_mode='FIXED')
        self.pack_current.modules.add(self.bi, self.flotte)
        self.pack_expired.modules.add(self.capteurs)
        for v, active, when in (('2.4.0', True, datetime.date(2026, 1, 10)), ('2.5.0', True, datetime.date(2026, 6, 1)),
                                ('1.9.0', False, datetime.date(2025, 3, 5))):
            cv = CoreVersion.objects.create(version=v, is_active=active)
            CoreVersion.objects.filter(pk=cv.pk).update(release_date=when)
        Category.objects.create(name='Vide', slug='vide')

    def get(self, name, key, **params):
        response = self.http.get(reverse(name), params)
        self.assertEqual(response.status_code, 200)
        return sorted(str(o) if key is None else getattr(o, key) for o in response.context['page'])

    # --- packs
    def test_bundles_by_text_status_and_discount_mode(self):
        self.assertEqual(self.get('backoffice:bundle_list', 'name', q='périmé'), ['Pack Périmé'])
        self.assertEqual(self.get('backoffice:bundle_list', 'name', active='0'), ['Pack Périmé'])
        self.assertEqual(self.get('backoffice:bundle_list', 'name', discount='FIXED'), ['Pack Périmé'])

    def test_bundles_by_validity_period(self):
        name = 'backoffice:bundle_list'
        self.assertEqual(self.get(name, 'name', validity='current'), ['Pack Actuel', 'Pack Ouvert'])
        self.assertEqual(self.get(name, 'name', validity='upcoming'), ['Pack Futur'])
        self.assertEqual(self.get(name, 'name', validity='expired'), ['Pack Périmé'])
        self.assertEqual(self.get(name, 'name', validity='unlimited'), ['Pack Ouvert'])

    def test_bundles_by_included_module_have_no_duplicates(self):
        self.assertEqual(self.get('backoffice:bundle_list', 'name', module=str(self.bi.pk)), ['Pack Actuel'])
        self.assertEqual(self.get('backoffice:bundle_list', 'name', module=str(self.capteurs.pk)), ['Pack Périmé'])

    def test_bundles_by_sales_and_start_date(self):
        buyer = User.objects.create_user('buyer', 'b@example.org', 'x')
        order = Order.objects.create(user=buyer, status='completed', total_amount=Decimal('10'))
        OrderItem.objects.create(order=order, bundle=self.pack_open, price_at_purchase=Decimal('10'))
        self.assertEqual(self.get('backoffice:bundle_list', 'name', sales='yes'), ['Pack Ouvert'])
        self.assertEqual(len(self.get('backoffice:bundle_list', 'name', sales='no')), 3)
        future = (timezone.now() + datetime.timedelta(days=2)).date().isoformat()
        self.assertEqual(self.get('backoffice:bundle_list', 'name', starts_from=future), ['Pack Futur'])

    # --- catégories
    def test_categories_by_text_and_module_count(self):
        name = 'backoffice:category_list'
        self.assertEqual(self.get(name, 'name', q='iot'), ['IoT'])
        self.assertEqual(self.get(name, 'name', modules='without'), ['Vide'])
        self.assertEqual(self.get(name, 'name', modules='with'), ['Analytics', 'IoT'])
        self.assertEqual(self.get(name, 'name', count_min='2', count_max='2'), ['Analytics', 'IoT'])
        self.assertEqual(self.get(name, 'name', count_min='3'), [])

    # --- versions du Core
    def test_core_versions_by_text_status_and_release_date(self):
        name = 'backoffice:core_version_list'
        self.assertEqual(self.get(name, 'version', q='2.4'), ['2.4.0'])
        self.assertEqual(self.get(name, 'version', active='0'), ['1.9.0'])
        self.assertEqual(self.get(name, 'version', released_from='2026-01-01', released_to='2026-03-01'), ['2.4.0'])
        self.assertEqual(self.get(name, 'version', released_to='2025-12-31'), ['1.9.0'])

    def test_every_catalog_list_shows_the_filter_bar_in_three_languages(self):
        for lang, expected in (('fr', 'Filtrer'), ('en', 'Filter'), ('nl', 'Filteren')):
            for name in ('backoffice:bundle_list', 'backoffice:category_list', 'backoffice:core_version_list'):
                with translation.override(lang):
                    url = reverse(name)
                self.assertContains(self.http.get(url), expected, msg_prefix=f'{name} {lang}')

    def test_garbage_parameters_are_ignored_on_catalog_lists(self):
        for name in ('backoffice:bundle_list', 'backoffice:category_list', 'backoffice:core_version_list'):
            response = self.http.get(reverse(name), {'validity': '??', 'discount': 'x', 'module': 'z', 'modules': '?',
                                                       'count_min': 'abc', 'released_from': 'nope', 'active': 'zz'})
            self.assertEqual(response.status_code, 200, name)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CustomersSalesFiltersTests(EngineFixtureMixin, TestCase):
    """Filtres des transactions, licences, installations, support client, utilisateurs et ventes (issue #27)."""

    def setUp(self):
        import uuid
        from catalog.models import ModuleBundle
        from licensing.models import Installation, License, SupportSubscription
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        self.make_fixtures()
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.http = HttpClient()
        self.http.login(username='admin_boss', password='AdminPassword123!')
        now = timezone.now()
        day = datetime.timedelta(days=1)

        # --- utilisateurs
        self.alice = User.objects.create_user('alice', 'alice@example.org', 'x', first_name='Alice', last_name='Martin',
                                              is_client=True, language_preference='fr')
        self.bob = User.objects.create_user('bob', 'bob@example.org', 'x', is_client=True, language_preference='en')
        self.carol = User.objects.create_user('carol', 'carol@example.org', 'x', is_staff=True, language_preference='en')
        self.dave = User.objects.create_user('dave', 'dave@example.org', 'x', is_client=True)
        self.eve = User.objects.create_user('eve', 'eve@example.org', 'x', is_client=True, is_active=False)

        # --- commandes
        self.pack = ModuleBundle.objects.create(name='Pack Suite', slug='pack-suite', short_description='x', description='x')
        self.pack.modules.add(self.bi)

        def order(user, status, amount, days_ago, ref='', waiver=True, module=None, bundle=None, product_type='module'):
            o = Order.objects.create(user=user, status=status, total_amount=Decimal(amount), stripe_payment_intent_id=ref,
                                     withdrawal_waiver_accepted_at=now if waiver else None)
            Order.objects.filter(pk=o.pk).update(created_at=now - days_ago * day)
            OrderItem.objects.create(order=o, module=module, bundle=bundle, price_at_purchase=Decimal(amount), product_type=product_type)
            return o
        self.o_alice = order(self.alice, 'completed', '200.00', 1, ref='pi_alice_111', module=self.bi)
        self.o_bob = order(self.bob, 'pending', '50.00', 10, ref='pi_bob_222', waiver=False, module=self.stock)
        self.o_pack = order(self.carol, 'completed', '400.00', 3, ref='pi_carol_333', bundle=self.pack)
        self.o_refund = order(self.alice, 'refunded', '120.50', 20, ref='pi_alice_444', module=self.bi)
        self.o_support = order(self.dave, 'completed', '40.00', 5, ref='pi_dave_555', module=self.bi, product_type='support')
        OrderItem.objects.create(order=self.o_alice, module=self.bi, price_at_purchase=Decimal('1'))   # même module deux fois : pas de doublon

        # --- installations et licences
        self.inst_linked = Installation.objects.create(user=self.alice, installation_uuid=uuid.uuid4(), company_name='Acme Industrie',
                                                       core_version='2.4.0')
        self.inst_orphan = Installation.objects.create(user=None, installation_uuid=uuid.uuid4(), company_name='Anonyme SPRL',
                                                       core_version='2.5.0')
        Installation.objects.filter(pk=self.inst_linked.pk).update(last_sync=now - 2 * day)
        Installation.objects.filter(pk=self.inst_orphan.pk).update(last_sync=now - 30 * day)
        self.lic_free = License.objects.create(user=self.alice, module=self.bi, max_activations=3, activation_count=1,
                                               installation=self.inst_linked)
        self.lic_full = License.objects.create(user=self.bob, module=self.stock, max_activations=1, activation_count=1)
        self.lic_off = License.objects.create(user=self.dave, module=self.flotte, is_active=False)
        License.objects.filter(pk=self.lic_off.pk).update(created_at=now - 40 * day)

        # --- support
        self.sub_active = SupportSubscription.objects.create(user=self.alice, module=self.bi, expires_at=now + 20 * day, amount_paid=Decimal('40'))
        self.sub_far = SupportSubscription.objects.create(user=self.bob, module=self.capteurs, expires_at=now + 60 * day, amount_paid=Decimal('90'))
        self.sub_expired = SupportSubscription.objects.create(user=self.dave, module=self.bi, expires_at=now - 5 * day, amount_paid=Decimal('40'))

        # --- compte supprimé (anonymisé) : ses licences et commandes sont conservées
        self.dave.anonymize()
        self.dave.refresh_from_db()

    def get(self, name, attr, **params):
        kwargs = params.pop('_kwargs', {})
        response = self.http.get(reverse(name, kwargs=kwargs), params)
        self.assertEqual(response.status_code, 200, f'{name} {params}')
        return sorted(getattr(o, attr) for o in response.context['page'])

    # --- transactions
    def test_orders_search_status_module_bundle(self):
        name = 'backoffice:order_list'
        self.assertEqual(self.get(name, 'pk', q='alice'), sorted([self.o_alice.pk, self.o_refund.pk]))
        self.assertEqual(self.get(name, 'pk', q='pi_bob'), [self.o_bob.pk])
        self.assertEqual(self.get(name, 'pk', q=f'#{self.o_pack.pk}'), [self.o_pack.pk])
        self.assertEqual(self.get(name, 'pk', status='refunded'), [self.o_refund.pk])
        self.assertEqual(self.get(name, 'pk', module=str(self.stock.pk)), [self.o_bob.pk])
        self.assertEqual(self.get(name, 'pk', bundle=str(self.pack.pk)), [self.o_pack.pk])

    def test_orders_module_filter_has_no_duplicates(self):
        got = self.get('backoffice:order_list', 'pk', module=str(self.bi.pk))
        self.assertEqual(len(got), len(set(got)))
        self.assertIn(self.o_alice.pk, got)          # deux lignes du même module dans la même commande

    def test_orders_amount_date_and_waiver(self):
        name = 'backoffice:order_list'
        self.assertEqual(self.get(name, 'pk', amount_min='100', amount_max='250'), sorted([self.o_alice.pk, self.o_refund.pk]))
        today = timezone.now().date()
        self.assertEqual(self.get(name, 'pk', created_from=(today - datetime.timedelta(days=4)).isoformat()),
                         sorted([self.o_alice.pk, self.o_pack.pk]))
        self.assertEqual(self.get(name, 'pk', waiver='0'), [self.o_bob.pk])
        self.assertEqual(len(self.get(name, 'pk', waiver='1')), 4)

    def test_orders_combined_and_dashboard_link(self):
        self.assertEqual(self.get('backoffice:order_list', 'pk', status='completed', q='alice', amount_min='150'), [self.o_alice.pk])
        response = self.http.get(reverse('backoffice:order_list') + '?status=completed')
        self.assertContains(response, '<option value="completed" selected>')

    # --- licences
    def test_licenses_search_by_key_with_and_without_dashes(self):
        name = 'backoffice:license_list'
        key = str(self.lic_free.license_key)
        self.assertEqual(self.get(name, 'pk', q=key), [self.lic_free.pk])
        self.assertEqual(self.get(name, 'pk', q=key.replace('-', '')), [self.lic_free.pk])
        self.assertEqual(self.get(name, 'pk', q=key[:8]), [self.lic_free.pk])
        self.assertEqual(self.get(name, 'pk', q='bob'), [self.lic_full.pk])

    def test_licenses_module_status_activations_installation_and_date(self):
        name = 'backoffice:license_list'
        self.assertEqual(self.get(name, 'pk', module=str(self.stock.pk)), [self.lic_full.pk])
        self.assertEqual(self.get(name, 'pk', active='0'), [self.lic_off.pk])
        self.assertEqual(self.get(name, 'pk', activations='available'), sorted([self.lic_free.pk, self.lic_off.pk]))
        self.assertEqual(self.get(name, 'pk', activations='full'), [self.lic_full.pk])
        self.assertEqual(self.get(name, 'pk', installed='1'), [self.lic_free.pk])
        self.assertEqual(self.get(name, 'pk', installed='0'), sorted([self.lic_full.pk, self.lic_off.pk]))
        old = (timezone.now() - datetime.timedelta(days=30)).date().isoformat()
        self.assertEqual(self.get(name, 'pk', purchased_to=old), [self.lic_off.pk])

    # --- installations
    def test_installations_by_uuid_company_version_link_and_licences(self):
        name = 'backoffice:installation_list'
        self.assertEqual(self.get(name, 'pk', q=str(self.inst_linked.installation_uuid)), [self.inst_linked.pk])
        self.assertEqual(self.get(name, 'pk', q='anonyme'), [self.inst_orphan.pk])
        self.assertEqual(self.get(name, 'pk', core='2.5.0'), [self.inst_orphan.pk])
        self.assertEqual(self.get(name, 'pk', linked='0'), [self.inst_orphan.pk])
        self.assertEqual(self.get(name, 'pk', linked='1'), [self.inst_linked.pk])
        self.assertEqual(self.get(name, 'pk', licensed='1'), [self.inst_linked.pk])
        self.assertEqual(self.get(name, 'pk', licensed='0'), [self.inst_orphan.pk])
        recent = (timezone.now() - datetime.timedelta(days=7)).date().isoformat()
        self.assertEqual(self.get(name, 'pk', synced_from=recent), [self.inst_linked.pk])

    # --- support client
    def test_support_clients_by_text_state_module_and_due_date(self):
        name = 'backoffice:support_subscription_search'
        self.assertEqual(self.get(name, 'pk', q='alice'), [self.alice.pk])
        self.assertEqual(self.get(name, 'pk', support='active'), sorted([self.alice.pk, self.bob.pk]))
        self.assertEqual(self.get(name, 'pk', support='expired'), [self.dave.pk])
        self.assertEqual(self.get(name, 'pk', module=str(self.capteurs.pk)), [self.bob.pk])
        self.assertEqual(self.get(name, 'pk', expiring='30'), [self.alice.pk])
        self.assertEqual(self.get(name, 'pk', expiring='90'), sorted([self.alice.pk, self.bob.pk]))

    def test_support_email_lookup_still_jumps_to_the_customer(self):
        response = self.http.get(reverse('backoffice:support_subscription_search'), {'email': 'alice@example.org'})
        self.assertRedirects(response, reverse('backoffice:user_detail', kwargs={'pk': self.alice.pk}), fetch_redirect_response=False)

    # --- utilisateurs
    def test_users_search_by_username_email_name_and_id(self):
        name = 'backoffice:user_list'
        self.assertEqual(self.get(name, 'pk', q='martin'), [self.alice.pk])
        self.assertEqual(self.get(name, 'pk', q='bob@'), [self.bob.pk])
        self.assertEqual(self.get(name, 'pk', q=f'#{self.carol.pk}'), [self.carol.pk])

    def test_users_by_account_type_status_and_language(self):
        name = 'backoffice:user_list'
        self.assertEqual(self.get(name, 'pk', type='staff'), [self.carol.pk])
        self.assertEqual(len(self.get(name, 'pk', type='admin')), 1)
        self.assertIn(self.alice.pk, self.get(name, 'pk', type='client'))
        self.assertEqual(self.get(name, 'pk', status='disabled'), [self.eve.pk])
        self.assertEqual(self.get(name, 'pk', language='en'), sorted([self.bob.pk, self.carol.pk]))
        self.assertIn(self.alice.pk, self.get(name, 'pk', language='fr'))
        # le modèle utilisateur ne propose que le français et l'anglais : une autre valeur est ignorée
        self.assertEqual(len(self.get(name, 'pk', language='nl')), User.objects.count())

    def test_deleted_anonymized_account_can_be_found_and_keeps_its_licences(self):
        name = 'backoffice:user_list'
        self.assertEqual(self.get(name, 'pk', status='deleted'), [self.dave.pk])
        self.assertNotIn(self.dave.pk, self.get(name, 'pk', status='active'))
        self.assertTrue(self.dave.username.startswith('deleted_'))
        self.assertEqual(self.get(name, 'pk', status='deleted', licenses='with'), [self.dave.pk])   # licence conservée
        self.assertEqual(self.get(name, 'pk', status='deleted', orders='with'), [self.dave.pk])

    def test_users_with_or_without_licences_orders_and_join_date(self):
        name = 'backoffice:user_list'
        self.assertIn(self.alice.pk, self.get(name, 'pk', licenses='with'))
        self.assertNotIn(self.carol.pk, self.get(name, 'pk', licenses='with'))
        self.assertIn(self.carol.pk, self.get(name, 'pk', licenses='without'))
        self.assertIn(self.eve.pk, self.get(name, 'pk', orders='without'))
        self.assertEqual(self.get(name, 'pk', joined_to='2000-01-01'), [])

    # --- détail des ventes d'un module
    def test_module_sales_filters(self):
        name, kw = 'backoffice:module_sales', {'_kwargs': {'pk': self.bi.pk}}
        self.assertEqual(self.get(name, 'order_id', q='pi_dave', **kw), [self.o_support.pk])
        self.assertEqual(self.get(name, 'order_id', type='support', **kw), [self.o_support.pk])
        self.assertEqual(self.get(name, 'order_id', type='pack', **kw), [self.o_pack.pk])
        self.assertEqual(self.get(name, 'order_id', status='refunded', **kw), [self.o_refund.pk])
        today = timezone.now().date()
        got = self.get(name, 'order_id', date_from=(today - datetime.timedelta(days=4)).isoformat(), **kw)
        self.assertIn(self.o_alice.pk, got)
        self.assertNotIn(self.o_refund.pk, got)

    def test_module_sales_statistics_ignore_the_filters_and_empty_messages(self):
        url = reverse('backoffice:module_sales', kwargs={'pk': self.bi.pk})
        plain = self.http.get(url).context['stats']
        self.assertEqual(self.http.get(url, {'status': 'refunded'}).context['stats'], plain)
        self.assertContains(self.http.get(url, {'q': 'introuvable'}), 'Aucune vente ne correspond à « introuvable »')
        self.assertContains(self.http.get(url, {'type': 'support', 'status': 'refunded'}), 'Aucune vente ne correspond aux filtres.')

    # --- transversal
    LISTS = ('backoffice:order_list', 'backoffice:license_list', 'backoffice:installation_list',
             'backoffice:support_subscription_search', 'backoffice:user_list')

    def test_filter_bar_is_present_in_three_languages(self):
        for lang, expected in (('fr', 'Filtrer'), ('en', 'Filter'), ('nl', 'Filteren')):
            for name in self.LISTS + ('backoffice:module_sales',):
                with translation.override(lang):
                    url = reverse(name, kwargs={'pk': self.bi.pk} if name.endswith('module_sales') else {})
                self.assertContains(self.http.get(url), expected, msg_prefix=f'{name} {lang}')

    def test_garbage_parameters_never_break_a_list(self):
        garbage = {'q': "' OR 1=1 --", 'status': '??', 'module': 'x', 'bundle': '9999999', 'amount_min': 'abc', 'created_from': 'nope',
                   'waiver': 'z', 'activations': '?', 'installed': '?', 'core': '?', 'linked': 'q', 'licensed': 'q', 'support': '?',
                   'expiring': '999', 'type': '?', 'language': '??', 'licenses': '?', 'orders': '?', 'joined_from': '2026-99-99'}
        for name in self.LISTS + ('backoffice:module_sales',):
            kwargs = {'pk': self.bi.pk} if name.endswith('module_sales') else {}
            self.assertEqual(self.http.get(reverse(name, kwargs=kwargs), garbage).status_code, 200, name)

    def test_filters_survive_pagination(self):
        for i in range(25):
            User.objects.create_user(f'bulk{i}', f'bulk{i}@example.org', 'x')
        response = self.http.get(reverse('backoffice:user_list'), {'q': 'bulk', 'per_page': '10'})
        self.assertEqual(response.context['page'].paginator.count, 25)
        self.assertRegex(response.content.decode(), r'href="\?[^"]*q=bulk[^"]*page=2')

    def test_lists_require_admin(self):
        for name in self.LISTS:
            self.assertNotEqual(HttpClient().get(reverse(name), {'q': 'x'}).status_code, 200, name)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ReviewsAndAuditLogFiltersTests(EngineFixtureMixin, TestCase):
    """Filtres des avis et du journal d'audit (issue #28) et présence du moteur sur toutes les listes."""

    def setUp(self):
        from backoffice.models import DatabaseAuditLog
        from catalog.models import ModuleBundle, Review
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        self.make_fixtures()
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.http = HttpClient()
        self.http.login(username='admin_boss', password='AdminPassword123!')
        now = timezone.now()
        day = datetime.timedelta(days=1)
        alice = User.objects.create_user('alice', 'alice@example.org', 'x')
        bob = User.objects.create_user('bob', 'bob@example.org', 'x')
        self.pack = ModuleBundle.objects.create(name='Pack Suite', slug='pack-suite', short_description='x', description='x')

        def review(user, rating, comment, approved, days_ago, module=None, bundle=None):
            r = Review.objects.create(user=user, module=module, bundle=bundle, rating=rating, comment=comment, is_approved=approved)
            Review.objects.filter(pk=r.pk).update(created_at=now - days_ago * day)
            return r
        self.r1 = review(alice, 5, 'Excellent outil de suivi', True, 1, module=self.bi)
        self.r2 = review(bob, 2, 'Trop cher pour ce que ça fait', False, 8, module=self.flotte)
        self.r3 = review(alice, 4, 'Le pack est pratique', False, 15, bundle=self.pack)
        self.r4 = review(bob, 5, 'Parfait', True, 30, module=self.bi)

        def log(action, table, row, old='', new='', days_ago=0):
            entry = DatabaseAuditLog.objects.create(action=action, table_name=table, row_id=row, old_values=old, new_values=new)
            DatabaseAuditLog.objects.filter(pk=entry.pk).update(timestamp=now - days_ago * day)
            return entry
        self.l1 = log('INSERT', 'payments_order', 101, new='{"status": "completed"}', days_ago=1)
        self.l2 = log('UPDATE', 'payments_order', 101, old='{"status": "pending"}', new='{"status": "refunded"}', days_ago=2)
        self.l3 = log('DELETE', 'licensing_license', 55, old='{"is_active": true}', days_ago=10)
        self.l4 = log('INSERT', 'licensing_license', 56, new='{"is_active": true}', days_ago=20)

    def get(self, name, attr='pk', **params):
        response = self.http.get(reverse(name), params)
        self.assertEqual(response.status_code, 200, f'{name} {params}')
        source = response.context['db_logs'] if name.endswith('logs_view') else response.context['reviews']
        return sorted(getattr(o, attr) for o in source)

    # --- avis
    def test_reviews_by_text_rating_status_module_and_target(self):
        name = 'backoffice:reviews_list'
        self.assertEqual(self.get(name, q='trop cher'), [self.r2.pk])
        self.assertEqual(self.get(name, q='alice'), sorted([self.r1.pk, self.r3.pk]))
        self.assertEqual(self.get(name, q='suite'), [self.r3.pk])                    # via le nom du pack
        self.assertEqual(self.get(name, rating='5'), sorted([self.r1.pk, self.r4.pk]))
        self.assertEqual(self.get(name, approved='0'), sorted([self.r2.pk, self.r3.pk]))
        self.assertEqual(self.get(name, approved='1'), sorted([self.r1.pk, self.r4.pk]))
        self.assertEqual(self.get(name, module=str(self.bi.pk)), sorted([self.r1.pk, self.r4.pk]))
        self.assertEqual(self.get(name, target='pack'), [self.r3.pk])
        self.assertEqual(len(self.get(name, target='module')), 3)

    def test_reviews_by_date_and_combination(self):
        name = 'backoffice:reviews_list'
        recent = (timezone.now() - datetime.timedelta(days=9)).date().isoformat()
        self.assertEqual(self.get(name, created_from=recent), sorted([self.r1.pk, self.r2.pk]))
        self.assertEqual(self.get(name, approved='0', rating='4'), [self.r3.pk])
        self.assertEqual(self.get(name, approved='1', q='parfait', rating='5'), [self.r4.pk])

    def test_validation_rate_is_computed_on_all_reviews_not_on_the_filtered_page(self):
        url = reverse('backoffice:reviews_list')
        plain = self.http.get(url).context
        filtered = self.http.get(url, {'approved': '1'}).context
        self.assertEqual(plain['total_count'], 4)
        self.assertEqual(filtered['total_count'], 4)
        self.assertEqual((filtered['approved_count'], filtered['pending_count']), (plain['approved_count'], plain['pending_count']))
        self.assertContains(self.http.get(url, {'approved': '1'}), '50%')

    # --- journal d'audit
    def test_audit_log_by_text_action_table_and_row(self):
        name = 'backoffice:logs_view'
        self.assertEqual(self.get(name, q='refunded'), [self.l2.pk])
        self.assertEqual(self.get(name, q='licensing_license'), sorted([self.l3.pk, self.l4.pk]))
        self.assertEqual(self.get(name, q='#101'), sorted([self.l1.pk, self.l2.pk]))
        self.assertEqual(self.get(name, action='DELETE'), [self.l3.pk])
        self.assertEqual(self.get(name, table='payments_order'), sorted([self.l1.pk, self.l2.pk]))
        self.assertEqual(self.get(name, action='INSERT', table='licensing_license'), [self.l4.pk])

    def test_audit_log_by_period(self):
        name = 'backoffice:logs_view'
        today = timezone.now().date()
        self.assertEqual(self.get(name, date_from=(today - datetime.timedelta(days=3)).isoformat()), sorted([self.l1.pk, self.l2.pk]))
        self.assertEqual(self.get(name, date_to=(today - datetime.timedelta(days=15)).isoformat()), [self.l4.pk])

    def test_audit_log_filter_bar_is_inside_the_database_tab(self):
        html = self.http.get(reverse('backoffice:logs_view'), {'action': 'DELETE'}).content.decode()
        tab = html[html.index('id="content-db"'):]
        self.assertIn('name="action"', tab)
        self.assertIn('name="table"', tab)
        self.assertNotIn('name="action"', html[:html.index('id="content-db"')])   # rien dans l'onglet du journal applicatif

    # --- transversal : toutes les listes du backoffice ont leur moteur de filtres
    ALL_LISTS = ('backoffice:module_list', 'backoffice:bundle_list', 'backoffice:category_list', 'backoffice:core_version_list',
                 'backoffice:order_list', 'backoffice:license_list', 'backoffice:installation_list',
                 'backoffice:support_subscription_search', 'backoffice:user_list', 'backoffice:reviews_list', 'backoffice:logs_view')

    def test_every_backoffice_list_has_a_translated_filter_bar_and_result_counter(self):
        expected = {'fr': ('Filtrer', 'résultat(s)'), 'en': ('Filter', 'result(s)'), 'nl': ('Filteren', 'resultaat/resultaten')}
        for lang, texts in expected.items():
            for name in self.ALL_LISTS + ('backoffice:module_sales',):
                with translation.override(lang):
                    url = reverse(name, kwargs={'pk': self.bi.pk} if name.endswith('module_sales') else {})
                response = self.http.get(url)
                self.assertEqual(response.status_code, 200, f'{name} {lang}')
                self.assertIn('filters', response.context, name)
                for text in texts:
                    self.assertContains(response, text, msg_prefix=f'{name} {lang}')

    def test_filters_never_leak_into_other_lists(self):
        # un paramètre propre à une liste n'a aucun effet sur une autre
        base = self.http.get(reverse('backoffice:module_list')).context['page'].paginator.count
        filtered = self.http.get(reverse('backoffice:module_list'), {'action': 'DELETE', 'rating': '1', 'status': 'refunded'})
        self.assertEqual(filtered.context['page'].paginator.count, base)


class EmptyListsAndRateRegressionTests(TestCase):
    """Compteur de résultats affiché même sur une liste vide ; taux de validation des avis non figé à 100 %."""

    def setUp(self):
        self.addCleanup(translation.activate, 'fr')
        translation.activate('fr')
        User.objects.create_superuser('admin_boss', 'admin@smartops.org', 'AdminPassword123!')
        self.http = HttpClient()
        self.http.login(username='admin_boss', password='AdminPassword123!')

    def test_empty_list_still_shows_zero_results(self):
        response = self.http.get(reverse('backoffice:core_version_list'))
        self.assertContains(response, '0 résultat(s)')

    def test_validation_rate_reflects_reviews_and_is_not_frozen_at_100(self):
        from catalog.models import Review
        category = Category.objects.create(name='C', slug='c')
        module = Module.objects.create(name='M', slug='m', category=category, price=Decimal('1'), is_active=True)
        user = User.objects.create_user('u', 'u@example.org', 'x')
        for approved in (True, False, False, False):
            Review.objects.create(user=user, module=module, rating=3, comment='x', is_approved=approved)
        self.assertContains(self.http.get(reverse('backoffice:reviews_list')), '25%')
        Review.objects.all().delete()
        self.assertContains(self.http.get(reverse('backoffice:reviews_list')), '100%')     # aucun avis : valeur neutre

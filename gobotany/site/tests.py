import json
import math
import re
import unittest

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.test.client import Client
from django.utils import timezone

from gobotany.core import models as core_models
from gobotany.dkey import models as dkey_models
from gobotany.plantshare import models as plantshare_models
from gobotany.search import models as search_models
from gobotany.site import models as site_models
from gobotany.site.templatetags import gobotany_tags

TEST_USERNAME = 'test'
TEST_EMAIL = 'test@test.com'
TEST_PASSWORD = 'testpass'

def _setup_sample_data():
    names = [ ('Abies balsamea', 'balsam fir'),
                ('Abutilon theophrasti', 'velvetleaf Indian-mallow'),
                ('Acalypha rhomboidea', 'common three-seeded-Mercury'),
                ('Acer negundo', 'ash-leaved maple'),
                ('Acer pensylvanicum', 'striped maple'),
                ('Acer platanoides', 'Norway maple'),
                ('Acer rubrum', 'red maple'),
                ('Acer saccharinum', 'silver maple'),
                ('Acer saccharum', 'sugar maple'),
                ('Acer spicatum', 'mountain maple'),
                ('Mimulus ringens', 'Allegheny monkey-flower'),
                ('Adlumia fungosa', 'Allegheny-vine'),
                ('Erythronium americanum', 'American trout-lily'),
                ('Echinochloa muricata', 'American barnyard grass'),
                ('Ammophila breviligulata', 'American beach grass'),
                ('Fagus grandifolia', 'American beech'),
                ('Celastrus scandens', 'American bittersweet'),
                ('Staphylea trifolia', 'American bladdernut'),
                ('Sparganium americanum', 'American bur-reed'),
                ('Erechtites hieraciifolius', 'American burnweed'),
                ('Amelanchier arborea', 'downy shadbush'),
                ('Amelanchier bartramiana', 'mountain shadbush'),
                ('Amelanchier canadensis', 'eastern shadbush'),
                ('Amelanchier laevis', 'smooth shadbush'),
                ('Amelanchier spicata', 'dwarf shadbush'),
                ('Castanea dentata', 'American chestnut'),
                ('Heracleum maximum', 'American cow-parsnip'),
                ('Viola labradorica', 'American dog violet'),
                ('Ulmus americana', 'American elm'),
                ('Veratrum viride', 'American false hellebore'),
                ('Hedeoma pulegioides', 'American false pennyroyal'),
                ('Cerastium strictum', 'American field chickweed'),
                ('Achillea millefolium', 'common yarrow'),
                ('Acorus americanus', 'several-veined sweetflag'),
                ('Acorus calamus', 'single-veined sweetflag'),
                ('Actaea pachypoda', 'white baneberry'),
                ('Actaea rubra', 'red baneberry'),
                ('Sabatia kennedyana', 'Plymouth rose-gentian'),
                ('Calystegia spithamaea', 'upright false bindweed'),
            ]
    for name in names:
        s = site_models.PlantNameSuggestion(name=name[0])
        s.save()
        s = site_models.PlantNameSuggestion(name=name[1])
        s.save()

    f = core_models.Family(name='Sapindaceae')
    f.save()

    g = core_models.Genus(name='Acer', family=f)
    g.save()
    t = core_models.Taxon(scientific_name='Acer rubrum', family=f, genus=g)
    t.save()

    gt = core_models.GlossaryTerm(term='aerial')
    gt.save()

    u = site_models.Update(date='2022-10-15')
    u.save()

    group, created = Group.objects.get_or_create(
        name=settings.AGREED_TO_TERMS_GROUP)
    user = User.objects.create_user(TEST_USERNAME, TEST_EMAIL,
        TEST_PASSWORD)
    # Add the test user to the "agreed to terms" group, so tests can
    # run as if the user already accepted the PlantShare Terms.
    group.user_set.add(user)

    # For a sighting, a timezone-aware date-time is required.
    current_tz = timezone.get_current_timezone()
    dt = datetime(year=2023, month=6, day=15, hour=12, minute=35,
        tzinfo=current_tz)
    s = plantshare_models.Sighting(user=user, identification='Acer rubrum',
        created=dt)
    s.save()

    q = plantshare_models.Question(question='What is this?',
        asked_by=user)
    q.save()

    pp = search_models.PlainPage(title='Help', url_path='/help/')
    pp.save()

    gl = search_models.GroupsListPage(title='Simple Key')
    gl.save()

    pg = core_models.PileGroup(name='Monocots', slug='monocots',
        friendly_title='Orchids and related plants')
    pg.save()
    pg2 = core_models.PileGroup(name='Graminoids', slug='graminoids',
        friendly_title='Grass-like plants')
    pg2.save()
    p = core_models.Pile(name='Orchids', slug='orchid-monocots',
        pilegroup=pg)
    p.save()

    sl = search_models.SubgroupsListPage(title='Orchids', group=pg)
    sl.save()
    sl2 = search_models.SubgroupsListPage(title='Graminoids', group=pg2)
    sl2.save()

    sr = search_models.SubgroupResultsPage(title='Orchids', subgroup=p,
        main_heading='Orchids')
    sr.save()

    p = dkey_models.Page(title='Group 1')
    p.save()


# Tests for PlantShare plant name picker API call

class PlantNameSuggestionsTests(TestCase):
    MAX_NAMES = 20

    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def half_max_names(self):
        return int(math.floor(self.MAX_NAMES / 2))


        response = self.client.get('/plant-name-suggestions/')
        self.assertEqual(200, response.status_code)

    def test_returns_json(self):
        response = self.client.get('/plant-name-suggestions/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_returns_names_in_expected_format(self):
        response = self.client.get('/plant-name-suggestions/?q=a')
        names = json.loads(response.content)
        for name in names:
            self.assertTrue(re.match(r'^[A-Za-z \-]*( \([A-Za-z \-]*\))?$',
                            name), 'Name "%s" not in expected format' % name)

    def test_returns_names_matching_at_beginning_of_string(self):
        EXPECTED_NAMES = [
            'Amelanchier arborea',
            'Amelanchier bartramiana',
            'Amelanchier canadensis',
            'Amelanchier laevis',
            'Amelanchier spicata',
            'American barnyard grass',
            'American beach grass',
            'American beech',
            'American bittersweet',
            'American bladdernut',
            ]
        response = self.client.get('/plant-name-suggestions/?q=ame')
        names = json.loads(response.content)
        self.assertEqual(names, EXPECTED_NAMES)

    def test_returns_results_with_interior_transposition(self):
        expected_names = ['Plymouth rose-gentian']
        response = self.client.get('/plant-name-suggestions/?q=pylmouth%20r')
        names = json.loads(response.content)
        self.assertEqual(names, expected_names)

    def test_returns_results_with_interior_transposition_second_word(self):
        expected_names = ['Plymouth rose-gentian']
        response = self.client.get(
            '/plant-name-suggestions/?q=plymouth%20rsoe')
        names = json.loads(response.content)
        self.assertEqual(names, expected_names)

    def test_returns_results_with_extra_character(self):
        expected_names = ['Plymouth rose-gentian']
        response = self.client.get('/plant-name-suggestions/?q=plymoutth%20r')
        names = json.loads(response.content)
        self.assertEqual(names, expected_names)

    def test_returns_results_with_missing_duplicate_character(self):
        expected_names = ['Sabatia kennedyana']
        response = self.client.get(
            '/plant-name-suggestions/?q=sabatia%20kened')
        names = json.loads(response.content)
        self.assertEqual(names, expected_names)


class RobotsTests(TestCase):

    def test_robots_returns_ok(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(200, response.status_code)


class UrlFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()

    def test_url_filter_taxon(self):
        obj = core_models.Taxon.objects.get(scientific_name='Acer rubrum')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/species/acer/rubrum/')

    def test_url_filter_family(self):
        obj = core_models.Family.objects.get(name='Sapindaceae')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/family/sapindaceae/')

    def test_url_filter_genus(self):
        obj = core_models.Genus.objects.get(name='Acer')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/genus/acer/')

    def test_url_filter_glossary_term(self):
        obj = core_models.GlossaryTerm.objects.get(term='aerial')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/glossary/a/#aerial')

    def test_url_filter_update(self):
        obj = site_models.Update.objects.first()
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/updates/#' + str(obj.id))

    def test_url_filter_sighting(self):
        obj = plantshare_models.Sighting.objects.first()
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/plantshare/sightings/' + str(obj.id) + '/')

    def test_url_filter_question(self):
        obj = plantshare_models.Question.objects.first()
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/plantshare/questions/all/' + \
            str(obj.asked.year) + '/#q' + str(obj.id))

    def test_url_filter_plain_page(self):
        obj = search_models.PlainPage.objects.first()
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/help/')

    def test_url_filter_groups_list_page(self):
        obj = search_models.GroupsListPage.objects.first()
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/simple/')

    def test_url_filter_subgroups_list_page(self):
        obj = search_models.SubgroupsListPage.objects.get(
            group__friendly_title='Orchids and related plants')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/simple/monocots/')

    def test_url_filter_subgroups_list_page_2(self):
        obj = search_models.SubgroupsListPage.objects.get(
            group__friendly_title='Grass-like plants')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/simple/graminoids/')

    def test_url_filter_subgroup_results_page(self):
        obj = search_models.SubgroupResultsPage.objects.get(
            main_heading='Orchids')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/simple/monocots/orchid-monocots/')

    def test_dkey_page(self):
        obj = dkey_models.Page.objects.get(title='Group 1')
        url = gobotany_tags.url(obj)
        self.assertEqual(url, '/dkey/group-1/')
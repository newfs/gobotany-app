import json
import math
import re
import unittest

from datetime import datetime

from django.test import TestCase
from django.test.client import Client

from gobotany.libtest import FunctionalCase
from gobotany.site import models as site_models

def _setup_sample_data():
    names = [   ('Abies balsamea', 'balsam fir'),
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
                ('Actaea rubra', ''),
            ]
    for name in names:
        s = site_models.PlantNameSuggestion(name=name[0])
        s.save()
        s = site_models.PlantNameSuggestion(name=name[1])
        s.save()


class HomeTests(FunctionalCase):

    def test_home_page(self):
        self.get('/')

        title = self.css1('title').text
        self.assertEqual(title, 'Go Botany: New England Wild Flower Society')

        get_started = self.css1('#cta')
        self.assertEqual(get_started.get_attribute('href'), '/simple/')
        self.assertEqual(get_started.text, 'Get Started')

    def test_groups_page(self):
        self.get('/simple/')

        h3 = self.css('h3')
        self.assertEqual(len(h3), 6)
        assert h3[0].text.startswith('Woody plants')
        assert h3[1].text.startswith('Aquatic plants')
        assert h3[2].text.startswith('Grass-like plants')
        assert h3[3].text.startswith('Orchids and related plants')
        assert h3[4].text.startswith('Ferns')
        assert h3[5].text.startswith('All other flowering non-woody plants')

        # Do group links get constructed correctly?

        e = self.css1('.plant-in-group')
        self.assertEqual('My plant is in this group', e.text)
        self.assertEqual(e.get_attribute('href'), '/simple/woody-plants/')

    def test_subgroups_page(self):
        self.get('/simple/ferns/')
        q = self.css('h3')
        self.assertEqual(len(q), 3)
        assert q[0].text.startswith('True ferns and moonworts')
        assert q[1].text.startswith('Clubmosses and relatives, plus quillworts')
        assert q[2].text.startswith('Horsetails and scouring-rushes')
        q = self.css('.plant-in-subgroup')
        self.assertTrue(
            q[0].get_attribute('href').endswith('/ferns/monilophytes/'))
        self.assertTrue(
            q[1].get_attribute('href').endswith('/ferns/lycophytes/'))
        self.assertTrue(
            q[2].get_attribute('href').endswith('/ferns/equisetaceae/'))

    def test_copyright_contains_current_year(self):
        self.get('/')
        copyright = self.css1('footer .copyright')
        current_year = str(datetime.now().year)
        self.assertIn(current_year, copyright.text)


class NavigationTests(FunctionalCase):

    def _get_anchor(self, path, label, parent_css_selector):
        self.get(path)
        e = self.css1(parent_css_selector)
        a = self.link_saying(label, e)
        return a

    # Header navigation items: linked, unlinked

    def test_header_home_item_is_linked(self):
        a = self._get_anchor('/about/', 'Home', 'header')
        self.assertTrue(a.get('href'))

    def test_header_home_item_is_unlinked(self):
        a = self._get_anchor('/', 'Home', 'header')
        self.assertFalse(a.get('href'))

    def test_header_simple_key_item_is_linked(self):
        a = self._get_anchor('/about/', 'Simple Key', 'header')
        self.assertTrue(a.get('href'))

    def test_header_simple_key_item_is_unlinked(self):
        a = self._get_anchor('/simple/', 'Simple Key', 'header')
        self.assertFalse(a.get('href'))

    def test_header_plantshare_item_is_linked(self):
        a = self._get_anchor('/about/', 'PlantShare', 'header')
        self.assertTrue(a.get('href'))

    @unittest.skip('Skip until release, because tests unaware of DEBUG')
    def test_header_plantshare_item_is_unlinked(self):
        a = self._get_anchor('/ps/', 'PlantShare', 'header')
        self.assertFalse(a.get('href'))

    def test_header_full_key_item_is_linked(self):
        a = self._get_anchor('/about/', 'Full Key', 'header')
        self.assertTrue(a.get('href'))

    @unittest.skip('Skip until release, because tests unaware of DEBUG')
    def test_header_full_key_item_is_unlinked(self):
        a = self._get_anchor('/full/', 'Full Key', 'header')
        self.assertFalse(a.get('href'))

    def test_header_dichotomous_key_item_is_linked(self):
        a = self._get_anchor('/about/', 'Dichotomous Key', 'header')
        self.assertTrue(a.get('href'))

    @unittest.skip('Skip until release, because tests unaware of DEBUG')
    def test_header_dichotomous_key_item_is_unlinked(self):
        a = self._get_anchor('/simple/', 'Dichotomous Key', 'header')
        self.assertFalse(a.get('href'))

    def test_header_teaching_item_is_linked(self):
        a = self._get_anchor('/about/', 'Teaching', 'header')
        self.assertTrue(a.get('href'))

    def test_header_teaching_item_is_unlinked(self):
        a = self._get_anchor('/teaching/', 'Teaching', 'header')
        self.assertFalse(a.get('href'))

    def test_header_about_item_is_linked(self):
        a = self._get_anchor('/', 'About', 'header')
        self.assertTrue(a.get('href'))

    def test_header_about_item_is_unlinked(self):
        a = self._get_anchor('/about/', 'About', 'header')
        self.assertFalse(a.get('href'))

    # Main headings of top pages in each section and a few within
    # (Style: these should match their navigation-item labels closely.)

    def test_main_heading_simple_key(self):
        self.get('/simple/')
        self.assertEqual(self.css1('#main h2').text,  # will become h1 soon
                         'Simple Key')

    def test_main_heading_simple_key_subgroups_list(self):
        self.get('/simple/woody-plants/')
        self.assertEqual(self.css1('#main h2').text,  # will become h1 soon
                         'Woody plants')

    def test_main_heading_plantshare(self):
        self.get('/ps/')
        self.assertEqual(self.css1('h1').text, 'PlantShare')

    def test_main_heading_full_key(self):
        self.get('/full/')
        self.assertEqual(self.css1('#main h2').text,  # will become h1 soon
                         'Full Key')

    def test_main_heading_full_key_subgroups_list(self):
        self.get('/full/ferns/')
        self.assertEqual(self.css1('#main h2').text,  # will become h1 soon
                         'Ferns')

    @unittest.skip('Skip for now: page returns error')
    def test_main_heading_dichotomous_key(self):
        self.get('/dkey/')
        self.assertEqual(self.css1('h1').text, 'Dichotomous Key')

    def test_main_heading_teaching(self):
        self.get('/teaching/')
        self.assertEqual(self.css1('h1').text, 'Teaching')

    def test_main_heading_about(self):
        self.get('/about/')
        self.assertEqual(self.css1('h1').text, 'About Go Botany')

    # Footer navigation items: linked, unlinked

    def test_footer_home_item_is_linked(self):
        a = self._get_anchor('/about/', 'Home', 'footer')
        self.assertTrue(a.get('href'))

    def test_footer_home_item_is_unlinked(self):
        a = self._get_anchor('/', 'Home', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_simple_key_item_is_linked(self):
        a = self._get_anchor('/about/', 'Simple Key', 'footer')
        self.assertTrue(a.get('href'))

    def test_footer_simple_key_item_is_unlinked(self):
        a = self._get_anchor('/simple/', 'Simple Key', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_plantshare_item_is_linked(self):
        a = self._get_anchor('/about/', 'PlantShare', 'footer')
        self.assertTrue(a.get('href'))

    @unittest.skip('Skip until release, because tests unaware of DEBUG')
    def test_footer_plantshare_item_is_unlinked(self):
        a = self._get_anchor('/ps/', 'PlantShare', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_full_key_item_is_linked(self):
        a = self._get_anchor('/about/', 'Full Key', 'footer')
        self.assertTrue(a.get('href'))

    @unittest.skip('Skip until release, because tests unaware of DEBUG')
    def test_footer_full_key_item_is_unlinked(self):
        a = self._get_anchor('/full/', 'Full Key', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_dichotomous_key_item_is_linked(self):
        a = self._get_anchor('/about/', 'Dichotomous Key', 'footer')
        self.assertTrue(a.get('href'))

    @unittest.skip('Skip until release, because tests unaware of DEBUG')
    def test_footer_dichotomous_key_item_is_unlinked(self):
        a = self._get_anchor('/simple/', 'Dichotomous Key', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_teaching_item_is_linked(self):
        a = self._get_anchor('/about/', 'Teaching', 'footer')
        self.assertTrue(a.get('href'))

    def test_footer_teaching_item_is_unlinked(self):
        a = self._get_anchor('/teaching/', 'Teaching', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_about_item_is_linked(self):
        a = self._get_anchor('/', 'About', 'footer')
        self.assertTrue(a.get('href'))

    def test_footer_about_item_is_unlinked(self):
        a = self._get_anchor('/about/', 'About', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_privacy_policy_item_is_linked(self):
        a = self._get_anchor('/about/', 'Privacy Policy', 'footer')
        self.assertTrue(a.get('href'))

    def test_footer_privacy_policy_item_is_unlinked(self):
        a = self._get_anchor('/privacy/', 'Privacy Policy', 'footer')
        self.assertFalse(a.get('href'))

    def test_footer_terms_of_use_item_is_linked(self):
        a = self._get_anchor('/about/', 'Terms of Use', 'footer')
        self.assertTrue(a.get('href'))

    def test_footer_terms_of_use_item_is_unlinked(self):
        a = self._get_anchor('/terms-of-use/', 'Terms of Use', 'footer')
        self.assertFalse(a.get('href'))


class GlossaryTests(FunctionalCase):

    def test_start_links_to_glossary(self):
        self.get('/start/')
        e = self.link_saying('Glossary')
        self.assertTrue(e.get('href').endswith('/glossary/'))

    def test_glossary_a_page_contains_a_terms(self):
        self.get('/glossary/a/')
        xterms = self.css('#terms dt')
        self.assertEqual(self.text(xterms[0])[0], 'a')
        self.assertEqual(self.text(xterms[-1])[0], 'a')

    def test_glossary_g_page_contains_g_terms(self):
        self.get('/glossary/g/')
        xterms = self.css('#terms dt')
        self.assertEqual(self.text(xterms[0])[0], 'g')
        self.assertEqual(self.text(xterms[-1])[0], 'g')

    def test_glossary_z_page_contains_z_terms(self):
        self.get('/glossary/z/')
        xterms = self.css('#terms dt')
        self.assertEqual(self.text(xterms[0])[0], 'z')
        self.assertEqual(self.text(xterms[-1])[0], 'z')

    def test_glossary_g_page_does_not_link_to_itself(self):
         self.get('/glossary/g/')
         e = self.link_saying('G')
         self.assertEqual(e.get('href'), None)

    def test_glossary_g_page_link_to_other_letters(self):
        self.get('/glossary/g/')
        for letter in 'ABCVWZ':  # 'X' and 'Y' currently have no terms
            e = self.links_saying(letter)
            self.assertTrue(len(e))

    def test_glossary_g_page_link_is_correct(self):
        self.get('/glossary/a/')
        e = self.link_saying('G')
        self.assertTrue(e.get('href').endswith('/glossary/g/'))


# Tests for PlantShare plant name picker API call

class PlantNameSuggestionsTestCase(TestCase):
    MAX_NAMES = 20

    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def half_max_names(self):
        return int(math.floor(self.MAX_NAMES / 2))

    def test_get_returns_ok(self):
        response = self.client.get('/plant-name-suggestions/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/plant-name-suggestions/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_names_in_expected_format(self):
        response = self.client.get('/plant-name-suggestions/?q=a')
        names = json.loads(response.content)
        for name in names:
            self.assertTrue(re.match(r'^[A-Za-z \-]*( \([A-Za-z \-]*\))?$',
                            name), 'Name "%s" not in expected format' % name)

    def test_get_returns_names_matching_at_beginning_of_string(self):
        EXPECTED_NAMES = [
            u'Amelanchier arborea',
            u'Amelanchier bartramiana',
            u'Amelanchier canadensis',
            u'Amelanchier laevis',
            u'Amelanchier spicata',
            u'American barnyard grass',
            u'American beach grass',
            u'American beech',
            u'American bittersweet',
            u'American bladdernut',
            ]
        response = self.client.get('/plant-name-suggestions/?q=ame')
        names = json.loads(response.content)
        self.assertEqual(names, EXPECTED_NAMES)


class RobotsTestCase(TestCase):

    def test_robots_returns_ok(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(200, response.status_code)


class SitemapTestCase(TestCase):

    def test_sitemap_returns_ok(self):
        response = self.client.get('/sitemap.txt')
        self.assertEqual(200, response.status_code)


class SpeciesListTestCase(TestCase):

    def test_species_list_returns_ok(self):
        response = self.client.get('/list/')
        self.assertEqual(200, response.status_code)

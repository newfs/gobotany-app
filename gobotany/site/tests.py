"""Tests of whether our basic site layout is present."""

import unittest

from datetime import datetime
from gobotany.libtest import FunctionalCase

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

    # Header navigation items

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

    # Footer navigation items

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

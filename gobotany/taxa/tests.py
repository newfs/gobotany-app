# -*- coding: utf-8 -*-
"""Tests for the taxa (family, genus, and species) pages."""

import re
from gobotany.libtest import FunctionalCase
from selenium.common.exceptions import NoSuchElementException


class FamilyTests(FunctionalCase):

    def test_family_page(self):
        self.get('/family/lycopodiaceae/')
        heading = self.css('#main h1')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text == 'Family: Lycopodiaceae')
        common_name = self.css('#main p.common')
        self.assertTrue(len(common_name))

    def test_family_page_has_example_images(self):
        self.get('/family/lycopodiaceae/')
        example_images = self.css('#main .pics a img')
        self.assertTrue(len(example_images))

    def test_family_page_has_list_of_genera(self):
        self.get('/family/lycopodiaceae/')
        genera = self.css('#main .genera li')
        self.assertTrue(len(genera))


class GenusTests(FunctionalCase):

    def test_genus_page(self):
        self.get('/genus/dendrolycopodium/')
        heading = self.css('#main h1')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text == 'Genus: Dendrolycopodium')
        common_name = self.css('#main p.common')
        self.assertTrue(len(common_name))
        self.assertTrue(common_name[0].text == 'tree-clubmoss')

    def test_genus_page_has_example_images(self):
        self.get('/genus/dendrolycopodium/')
        example_images = self.css('#main .pics a img')
        self.assertTrue(len(example_images))

    def test_genus_page_has_family_link(self):
        self.get('/genus/dendrolycopodium/')
        family_link = self.css('#main p.family a')
        self.assertTrue(len(family_link))

    def test_genus_page_has_list_of_species(self):
        self.get('/genus/dendrolycopodium/')
        species = self.css('#main .species li')
        self.assertTrue(len(species))


class SpeciesPageTests(FunctionalCase):

    def crumb(self, n):
        return self.text(self.css('#breadcrumb a')[n])

    def test_simple_key_species_page_has_breadcrumb(self):
        self.get('/species/adiantum/pedatum/')
        self.assertTrue(self.css1('#breadcrumb'))

    # Test breadcrumb trails for a species included in the Simple Key, and
    # a species not included in the Simple Key. These should have
    # breadcrumbs for the Simple and Full Keys, respectively.  

    def test_simplekey_species_breadcrumbs(self):
        self.get('/species/dendrolycopodium/dendroideum/?pile=lycophytes')
        self.assertEqual(self.crumb(0), u'Simple Key')
        self.assertEqual(self.crumb(1), u'Ferns')
        self.assertEqual(self.crumb(2),
                         u'Clubmosses and relatives, plus quillworts')

    def test_fullkey_species_breadcrumbs(self):
        self.get('/species/diphasiastrum/complanatum/?pile=lycophytes')
        self.assertEqual(self.crumb(0), u'Full Key')
        self.assertEqual(self.crumb(1), u'Ferns')
        self.assertEqual(self.crumb(2),
                         u'Clubmosses and relatives, plus quillworts')

    # Test breadcrumb trails for the same species, but coming from the
    # Dichotomous Key. Both should have Dichotomous Key breadcrumbs.

    def test_simplekey_species_dichotomous_breadcrumbs(self):
        self.get('/species/dendrolycopodium/dendroideum/?key=dichotomous')
        self.assertEqual(self.crumb(0), u'Dichotomous Key')
        self.assertEqual(self.crumb(1), u'Group 1: Lycophytes, Monilophytes')
        self.assertEqual(self.crumb(2), u'Family Lycopodiaceae')

    def test_fullkey_species_dichotomous_breadcrumbs(self):
        self.get('/species/diphasiastrum/complanatum/?key=dichotomous')
        self.assertEqual(self.crumb(0), u'Dichotomous Key')
        self.assertEqual(self.crumb(1), u'Group 1: Lycophytes, Monilophytes')
        self.assertEqual(self.crumb(2), u'Family Lycopodiaceae')

    # Test photo titles and credits.

    def _photos_have_expected_caption_format(self, species_page_url):
        # For a species page, make sure the plant photos have the expected
        # format for title/alt text that gets formatted on the fly atop 
        # each photo when it is viewed large. The text should contain a
        # title, image type, contributor, copyright holder. It can also
        # optionally have a "source" note at the end.
        REGEX_PATTERN = '.*: .*\. ~ By .*\. ~ Copyright .*\s+.( ~ .\s+)?'
        self.get(species_page_url)
        links = self.css('#species-images a')
        self.assertTrue(len(links))
        for link in links:
            title = link.get_attribute('title')
            self.assertTrue(re.match(REGEX_PATTERN, title))
        images = self.css('#species-images a img')
        self.assertTrue(len(images))
        for image in images:
            alt_text = image.get_attribute('alt')
            self.assertTrue(re.match(REGEX_PATTERN, alt_text))

    def test_species_page_photos_have_title_credit_copyright(self):
        species_page_url = '/species/dendrolycopodium/dendroideum/'
        self._photos_have_expected_caption_format(species_page_url)

    def test_species_page_photos_have_title_credit_copyright_source(self):
        # Some images on this page have "sources" specified for them.
        species_page_url = ('/species/gymnocarpium/dryopteris/')
        self._photos_have_expected_caption_format(species_page_url)

    # Temporarily, non-Simple-Key pages show a data disclaimer.

    def test_non_simple_key_species_page_has_note_about_data(self):
        self.get('/species/adiantum/aleuticum/')
        note = self.css('.content .note')[0].text
        self.assertEqual(note, ('Data collection in progress. Complete data '
                                'coming soon.'))

class LookalikesTests(FunctionalCase):

    def test_lookalikes_are_in_search_indexes_for_many_pages(self):
        self.get('/search/?q=sometimes+confused+with')
        page_links = self.css('.search-navigation li')
        self.assertTrue(len(page_links) > 10)   # more than 100 results

    def test_species_pages_have_lookalikes(self):
        # Verify a sampling of the species expected to have lookalikes.
        SPECIES = ['Huperzia appressa', 'Lonicera dioica', 'Actaea rubra',
                   'Digitalis purpurea', 'Brachyelytrum aristosum']
        for s in SPECIES:
            url = '/species/%s/' % s.replace(' ', '/').lower()
            self.get(url)
            heading = self.css('#sidebar .lookalikes h4')
            self.assertTrue(heading)
            lookalikes = self.css('#sidebar .lookalikes dt')
            self.assertTrue(len(lookalikes) > 0)
            for lookalike in lookalikes:
                self.assertTrue(len(lookalike.text) > 0)
            notes = self.css('#sidebar .lookalikes dd')
            self.assertTrue(len(notes) > 0)
            for note in notes:
                self.assertTrue(len(note.text) > 0)

    def test_lookalikes_with_notes(self):
        self.get('/species/abies/balsamea/')
        lookalike = self.css('#sidebar .lookalikes dt')[0].text
        notes = self.css('#sidebar .lookalikes dd')[0].text
        self.assertTrue(lookalike.find(':') > -1);
        self.assertTrue(len(notes) > 0)
        self.assertTrue(notes.find('winter buds not resinous,') > -1)

    def test_lookalikes_without_notes(self):
        self.get('/species/abies/concolor/')
        lookalike = self.css('#sidebar .lookalikes dt')[0].text
        notes = self.css('#sidebar .lookalikes dd')[0].text
        self.assertTrue(lookalike.find(':') == -1);
        self.assertTrue(len(notes) == 0)

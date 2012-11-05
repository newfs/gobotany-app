# -*- coding: utf-8 -*-
"""Tests for the Simple and Full Keys."""

import re
from gobotany.libtest import FunctionalCase
from selenium.common.exceptions import NoSuchElementException


class SimpleKeyTests(FunctionalCase):

    def test_simple_first_level_page_title(self):
        self.get('/simple/')
        title = self.css1('title').text
        self.assertEqual(title,
            'Simple Key for Plant Identification: Go Botany')

    def test_simple_first_level_page_main_heading(self):
        self.get('/simple/')
        heading = self.css1('#main h2').text
        self.assertEqual(heading, 'Simple Key')


class FullKeyTests(FunctionalCase):

    def test_full_first_level_page_title(self):
        self.get('/full/')
        title = self.css1('title').text
        self.assertEqual(title,
            'Full Key for Plant Identification: Go Botany')

    def test_full_first_level_page_main_heading(self):
        self.get('/full/')
        heading = self.css1('#main h2').text
        self.assertEqual(heading, 'Full Key')


class SpeciesPageTests(FunctionalCase):

    def crumb(self, n):
        return self.text(self.css('#breadcrumb a')[n])

    def test_simplekey_species_breadcrumbs(self):
        self.get('/species/dendrolycopodium/dendroideum/?pile=lycophytes')
        self.assertEqual(self.crumb(0), u'Simple Key')
        self.assertEqual(self.crumb(1), u'Ferns')
        self.assertEqual(self.crumb(2),
                         u'Clubmosses and relatives, plus quillworts')

    def test_simplekey_species_dichotomous_breadcrumbs(self):
        self.get('/species/dendrolycopodium/dendroideum/?key=dichotomous')
        self.assertEqual(self.crumb(0), u'« Back to the Key to the Families')
        self.assertEqual(self.crumb(1), u'« Group 1: Lycophytes, Monilophytes')
        self.assertEqual(self.crumb(2), u'« Family Lycopodiaceae')

    def test_fullkey_species_breadcrumbs(self):
        self.get('/species/diphasiastrum/complanatum/?pile=lycophytes')
        self.assertEqual(self.crumb(0), u'Full Key')
        self.assertEqual(self.crumb(1), u'Ferns')
        self.assertEqual(self.crumb(2),
                         u'Clubmosses and relatives, plus quillworts')

    def test_fullkey_species_dichotomous_breadcrumbs(self):
        self.get('/species/diphasiastrum/complanatum/?key=dichotomous')
        self.assertEqual(self.crumb(0), u'« Back to the Key to the Families')
        self.assertEqual(self.crumb(1), u'« Group 1: Lycophytes, Monilophytes')
        self.assertEqual(self.crumb(2), u'« Family Lycopodiaceae')

    #

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

    def test_simple_key_species_page_has_breadcrumb(self):
        self.get('/species/adiantum/pedatum/')
        self.assertTrue(self.css1('#breadcrumb'))

    def test_non_simple_key_species_page_omits_breadcrumb(self):
        # Breadcrumb should be omitted until Full Key is implemented.
        self.get('/species/adiantum/aleuticum/')
        breadcrumb = None
        try:
            breadcrumb = self.css1('#breadcrumb')
        except NoSuchElementException:
            self.assertEqual(breadcrumb, None)
            pass

    def test_non_simple_key_species_page_has_note_about_data(self):
        # Temporarily, non-Simple-Key pages show a data disclaimer.
        self.get('/species/adiantum/aleuticum/')
        note = self.css('.content .note')[0].text
        self.assertEqual(note, ('Data collection in progress. Complete data '
                                'are coming soon.'))

# -*- coding: utf-8 -*-
"""Tests for the Simple and Full Keys."""

from gobotany.libtest import FunctionalCase


class SimpleKeyTests(FunctionalCase):

    def test_simple_first_level_page_title(self):
        self.get('/simple/')
        title = self.css1('title').text
        self.assertEqual(title,
            'Simple Key for Plant Identification: Go Botany')

    def test_simple_first_level_page_main_heading(self):
        self.get('/simple/')
        heading = self.css1('h1').text
        self.assertEqual(heading, 'Simple Key')

    def test_groups_page(self):
        self.get('/simple/')

        h = self.css('h2')
        self.assertEqual(len(h), 6)
        assert h[0].text.startswith('Woody plants')
        assert h[1].text.startswith('Aquatic plants')
        assert h[2].text.startswith('Grass-like plants')
        assert h[3].text.startswith('Orchids and related plants')
        assert h[4].text.startswith('Ferns')
        assert h[5].text.startswith('All other flowering non-woody plants')

        # Do group links get constructed correctly?

        e = self.css1('.plant-in-group')
        self.assertEqual('My plant is in this group', e.text)
        self.assertEqual(e.get_attribute('href'), '/simple/woody-plants/')

    def test_subgroups_page(self):
        self.get('/simple/ferns/')
        h = self.css('h2')
        self.assertEqual(len(h), 3)
        assert h[0].text.startswith('True ferns and moonworts')
        assert h[1].text.startswith('Clubmosses and relatives, plus quillworts')
        assert h[2].text.startswith('Horsetails and scouring-rushes')
        e = self.css('.plant-in-subgroup')
        self.assertTrue(
            e[0].get_attribute('href').endswith('/ferns/monilophytes/'))
        self.assertTrue(
            e[1].get_attribute('href').endswith('/ferns/lycophytes/'))
        self.assertTrue(
            e[2].get_attribute('href').endswith('/ferns/equisetaceae/'))


class FullKeyTests(FunctionalCase):

    def test_full_first_level_page_title(self):
        self.get('/full/')
        title = self.css1('title').text
        self.assertEqual(title,
            'Full Key for Plant Identification: Go Botany')

    def test_full_first_level_page_main_heading(self):
        self.get('/full/')
        heading = self.css1('h1').text
        self.assertEqual(heading, 'Full Key')

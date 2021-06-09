# -*- coding: utf-8 -*-
"""Tests for the Simple and Full Keys."""

import unittest
from gobotany.core import models
from gobotany.simplekey.templatetags.simplekey_extras import habitat_names
from gobotany.libtest import FunctionalCase, TestCase


# Uncomment the line below to skip tests that run against the real database.
#@unittest.skip('Skipping tests that run against the real database')
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

        e = self.css1('#main .action-link')
        self.assertEqual('My plant is in this group', e.text)
        self.assertEqual(e.get_attribute('href'), '/simple/woody-plants/')

    def test_subgroups_page(self):
        self.get('/simple/ferns/')
        h = self.css('h2')
        self.assertEqual(len(h), 3)
        assert h[0].text.startswith('True ferns and moonworts')
        assert h[1].text.startswith('Clubmosses and relatives, plus quillworts')
        assert h[2].text.startswith('Horsetails and scouring-rushes')
        e = self.css('#main .action-link')
        self.assertTrue(
            e[0].get_attribute('href').endswith('/ferns/monilophytes/'))
        self.assertTrue(
            e[1].get_attribute('href').endswith('/ferns/lycophytes/'))
        self.assertTrue(
            e[2].get_attribute('href').endswith('/ferns/equisetaceae/'))


# Uncomment the line below to skip tests that run against the real database.
#@unittest.skip('Skipping tests that run against the real database')
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


habitat_data = [

    # Habitat names are important enough that we actually do an explicit
    # check of every single one of them, to make sure that they look
    # good on the screen.  These entries all have the format:
    #
    # (value_str, friendly_text,    <-- inputs from character value
    #  expected_name)               <-- output of habitat_names()

    ('alpine/subalpine', 'alpine or subalpine zones',
     'alpine or subalpine zones'),
    ('anthropogenic', 'man-made or disturbed habitats',
     'anthropogenic (man-made or disturbed habitats)'),
    ('bogs', 'bogs',
     'bogs'),
    ('brackish tidal marsh/flat', 'brackish or salt marshes and flats',
     'brackish or salt marshes and flats'),
    ('cliffs/balds', 'cliffs, balds, or ledges',
     'cliffs, balds, or ledges'),
    ('coastal beaches', 'sea beaches',
     'coastal beaches (sea beaches)'),
    ('dunes', 'dunes',
     'dunes'),
    ('fens', 'fens (calcium-rich wetlands)',
     'fens (calcium-rich wetlands)'),
    ('floodplain', 'river or stream floodplains',
     'floodplain (river or stream floodplains)'),
    ('forest edges', 'edges of forests',
     'forest edges'),
    ('forests', 'forests',
     'forests'),
    ('fresh tidal marsh/flat', 'fresh tidal marshes or flats',
     'fresh tidal marshes or flats'),
    ('grassland', 'grasslands',
     'grassland'),
    ('lacustrine', 'in lakes or ponds',
     'lacustrine (in lakes or ponds)'),
    ('marshes', 'marshes',
     'marshes'),
    ('meadows and fields', 'meadows or fields',
     'meadows and fields'),
    ('mountain summits', 'mountain summits and plateaus',
     'mountain summits and plateaus'),
    ('ocean intertidal/subtidal', 'intertidal, subtidal or open ocean',
     'intertidal, subtidal or open ocean'),
    ('ridges/ledges', 'ridges or ledges',
     'ridges or ledges'),
    ('river/lakeshores', 'shores of rivers or lakes',
     'shores of rivers or lakes'),
    ('riverine', 'in rivers or streams',
     'riverine (in rivers or streams)'),
    ('sandplains and barrens', 'sandplains or barrens',
     'sandplains and barrens'),
    ('shrubland/thicket', 'shrublands or thickets',
     'shrublands or thickets'),
    ('swamps', 'swamps',
     'swamps'),
    ('talus and rocky slopes', 'talus or rocky slopes',
     'talus and rocky slopes'),
    ('wetland margins', 'edges of wetlands',
     'wetland margins (edges of wetlands)'),
    ('woodlands', 'woodlands',
     'woodlands'),
    ]

class UnitTests(TestCase):

    def test_habitat_names(self):
        for value_str, friendly_text, expected_name in habitat_data:
            cv = models.CharacterValue()
            cv.value_str = value_str
            cv.friendly_text = friendly_text
            cvlist = [cv]
            namelist = habitat_names(cvlist)
            self.assertEqual(expected_name, namelist[0])

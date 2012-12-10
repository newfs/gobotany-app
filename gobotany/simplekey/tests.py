# -*- coding: utf-8 -*-
"""Tests for the Simple and Full Keys."""

from gobotany.core import models
from gobotany.simplekey.templatetags.simplekey_extras import habitat_names
from gobotany.libtest import FunctionalCase, TestCase


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


habitat_data = [

    # These entries all have the format:
    #
    # (value_str, friendly_text,    <-- inputs
    #  expected_name)               <-- output

    (u'alpine/subalpine', u'alpine or subalpine zones',
     u'alpine or subalpine zones'),
    (u'anthropogenic', u'man-made or disturbed habitats',
     u'anthropogenic (man-made or disturbed habitats)'),
    (u'bogs', u'bogs',
     u'bogs'),
    (u'brackish tidal marsh/flat', u'brackish or salt marshes and flats',
     u'brackish or salt marshes and flats'),
    (u'cliffs/balds', u'cliffs, balds, or ledges',
     u'cliffs, balds, or ledges'),
    (u'coastal beaches', u'sea beaches',
     u'coastal beaches (sea beaches)'),
    (u'dunes', u'dunes',
     u'dunes'),
    (u'fens', u'fens (calcium-rich wetlands)',
     u'fens (calcium-rich wetlands)'),
    (u'floodplain', u'river or stream floodplains',
     u'floodplain (river or stream floodplains)'),
    (u'forest edges', u'edges of forests',
     u'forest edges'),
    (u'forests', u'forests',
     u'forests'),
    (u'fresh tidal marsh/flat', u'fresh tidal marshes or flats',
     u'fresh tidal marshes or flats'),
    (u'grassland', u'grasslands',
     u'grassland'),
    (u'lacustrine', u'in lakes or ponds',
     u'lacustrine (in lakes or ponds)'),
    (u'marshes', u'marshes',
     u'marshes'),
    (u'meadows and fields', u'meadows or fields',
     u'meadows and fields'),
    (u'mountain summits', u'mountain summits and plateaus',
     u'mountain summits and plateaus'),
    (u'ocean intertidal/subtidal', u'intertidal, subtidal or open ocean',
     u'intertidal, subtidal or open ocean'),
    (u'ridges/ledges', u'ridges or ledges',
     u'ridges or ledges'),
    (u'river/lakeshores', u'shores of rivers or lakes',
     u'shores of rivers or lakes'),
    (u'riverine', u'in rivers or streams',
     u'riverine (in rivers or streams)'),
    (u'sandplains and barrens', u'sandplains or barrens',
     u'sandplains and barrens'),
    (u'shrubland/thicket', u'shrublands or thickets',
     u'shrublands or thickets'),
    (u'swamps', u'swamps',
     u'swamps'),
    (u'talus and rocky slopes', u'talus or rocky slopes',
     u'talus and rocky slopes'),
    (u'wetland margins', u'edges of wetlands',
     u'wetland margins (edges of wetlands)'),
    (u'woodlands', u'woodlands',
     u'woodlands'),
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

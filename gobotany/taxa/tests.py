# -*- coding: utf-8 -*-
"""Tests for the taxa (family, genus, and species) pages."""

import re
import unittest

from django.template import Context, Template
from django.test import TestCase

from gobotany.libtest import FunctionalCase


# Uncomment the line below to skip tests that run against the real database.
#@unittest.skip('Skipping tests that run against the real database')
class FamilyTests(FunctionalCase):

    def test_family_page(self):
        self.get('/family/lycopodiaceae/')
        heading = self.css('#main h1')
        self.assertTrue(len(heading))
        self.assertTrue(
            heading[0].text == 'Family: Lycopodiaceae — club moss family')

    @unittest.skip('This test fails when run with the api or core tests.')
    def test_family_page_has_example_images(self):
        response = self.get('/family/lycopodiaceae/')
        example_images = self.css('#main .pics a img')
        print('example_images:', example_images)
        self.assertTrue(len(example_images))

    def test_family_page_has_list_of_genera(self):
        self.get('/family/lycopodiaceae/')
        genera = self.css('#main .genera li')
        self.assertTrue(len(genera))


# Uncomment the line below to skip tests that run against the real database.
#@unittest.skip('Skipping tests that run against the real database')
class GenusTests(FunctionalCase):

    def test_genus_page(self):
        self.get('/genus/dendrolycopodium/')
        heading = self.css('#main h1')
        self.assertTrue(len(heading))
        self.assertTrue(
            heading[0].text == 'Genus: Dendrolycopodium — tree-clubmoss')

    @unittest.skip('This test fails when run with the api or core tests.')
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


# Uncomment the line below to skip tests that run against the real database.
#@unittest.skip('Skipping tests that run against the real database')
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
        self.assertEqual(self.crumb(0), 'Simple Key')
        self.assertEqual(self.crumb(1), 'Ferns')
        self.assertEqual(self.crumb(2),
                         'Clubmosses and relatives, plus quillworts')

    def test_fullkey_species_breadcrumbs(self):
        self.get('/species/diphasiastrum/complanatum/?pile=lycophytes')
        self.assertEqual(self.crumb(0), 'Full Key')
        self.assertEqual(self.crumb(1), 'Ferns')
        self.assertEqual(self.crumb(2),
                         'Clubmosses and relatives, plus quillworts')

    # Test breadcrumb trails for the same species, but coming from the
    # Dichotomous Key. Both should have Dichotomous Key breadcrumbs.

    def test_simplekey_species_dichotomous_breadcrumbs(self):
        self.get('/species/dendrolycopodium/dendroideum/?key=dichotomous')
        self.assertEqual(self.crumb(0), 'Dichotomous Key')
        self.assertEqual(self.crumb(1), 'Lycopodiaceae')
        self.assertEqual(self.crumb(2), 'Dendrolycopodium')

    def test_fullkey_species_dichotomous_breadcrumbs(self):
        self.get('/species/diphasiastrum/complanatum/?key=dichotomous')
        self.assertEqual(self.crumb(0), 'Dichotomous Key')
        self.assertEqual(self.crumb(1), 'Lycopodiaceae')
        self.assertEqual(self.crumb(2), 'Diphasiastrum')

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

    @unittest.skip('This test fails when run with the api or core tests.')
    def test_species_page_photos_have_title_credit_copyright(self):
        species_page_url = '/species/dendrolycopodium/dendroideum/'
        self._photos_have_expected_caption_format(species_page_url)

    @unittest.skip('This test fails when run with the api or core tests.')
    def test_species_page_photos_have_title_credit_copyright_source(self):
        # Some images on this page have "sources" specified for them.
        species_page_url = ('/species/gymnocarpium/dryopteris/')
        self._photos_have_expected_caption_format(species_page_url)


# Uncomment the line below to skip tests that run against the real database.
#@unittest.skip('Skipping tests that run against the real database')
class LookalikesTests(FunctionalCase):

    def test_species_pages_have_lookalikes(self):
        # Verify a sampling of the species expected to have lookalikes.
        SPECIES = ['Huperzia appressa', 'Lonicera dioica', 'Actaea rubra',
                   'Digitalis purpurea', 'Brachyelytrum aristosum']
        for s in SPECIES:
            url = '/species/%s/' % s.replace(' ', '/').lower()
            self.get(url)
            heading = self.css('#side .lookalikes h2')
            self.assertTrue(heading)
            lookalikes = self.css('#side .lookalikes dt')
            self.assertTrue(len(lookalikes) > 0)
            for lookalike in lookalikes:
                self.assertTrue(len(lookalike.text) > 0)
            notes = self.css('#side .lookalikes dd')
            self.assertTrue(len(notes) > 0)
            for note in notes:
                self.assertTrue(len(note.text) > 0)

    def test_lookalikes_with_notes(self):
        self.get('/species/abies/balsamea/')
        lookalike = self.css('#side .lookalikes dt')[0].text
        notes = self.css('#side .lookalikes dd')[0].text
        self.assertTrue(lookalike.find(':') > -1);
        self.assertTrue(len(notes) > 0)
        self.assertTrue(notes.find('winter buds not resinous,') > -1)

    def test_lookalikes_without_notes(self):
        self.get('/species/abies/concolor/')
        lookalike = self.css('#side .lookalikes dt')[0].text
        notes = self.css('#side .lookalikes dd')[0].text
        self.assertTrue(lookalike.find(':') == -1);
        self.assertTrue(len(notes) == 0)


class TemplateTagTestCase(TestCase):

    def render_template(self, template_contents, context={}):
        t = Template(template_contents)
        c = Context(context)
        return t.render(c)


class SRankLabelTests(TemplateTagTestCase):

    def label_for_code(self, code):
        template = (
            '{{% load taxa_tags %}}'
            '{{% s_rank_label "{code}" %}}'
        ).format(code=code)
        return self.render_template(template)

    def test_s_rank_s1(self):
        self.assertEqual(self.label_for_code('S1'), 'extremely rare')

    def test_s_rank_s1s2(self):
        self.assertEqual(self.label_for_code('S1S2'),
            'extremely rare to rare')

    def test_s_rank_s1s3(self):
        self.assertEqual(self.label_for_code('S1S3'),
            'extremely rare to uncommon')

    def test_s_rank_s2(self):
        self.assertEqual(self.label_for_code('S2'), 'rare')

    def test_s_rank_s2s3(self):
        self.assertEqual(self.label_for_code('S2S3'), 'rare to uncommon')

    def test_s_rank_s2s4(self):
        self.assertEqual(self.label_for_code('S2S4'),
            'rare to fairly widespread')

    def test_s_rank_s3(self):
        self.assertEqual(self.label_for_code('S3'), 'uncommon')

    def test_s_rank_s3s4(self):
        self.assertEqual(self.label_for_code('S3S4'),
            'uncommon to fairly widespread')

    def test_s_rank_s3s5(self):
        self.assertEqual(self.label_for_code('S3S5'),
            'uncommon to widespread')

    def test_s_rank_s4(self):
        self.assertEqual(self.label_for_code('S4'), 'fairly widespread')

    def test_s_rank_s5(self):
        self.assertEqual(self.label_for_code('S5'), 'widespread')

    def test_s_rank_sh(self):
        self.assertEqual(self.label_for_code('SH'), 'historical')

    def test_s_rank_sna(self):
        self.assertEqual(self.label_for_code('SNA'), 'not applicable')

    def test_s_rank_snr(self):
        self.assertEqual(self.label_for_code('SNR'), 'unranked')

    def test_s_rank_su(self):
        self.assertEqual(self.label_for_code('SU'), 'unrankable')

    def test_s_rank_sx(self):
        self.assertEqual(self.label_for_code('SX'), 'extirpated')

    def test_s_rank_is_uncertain(self):
        # "Uncertain" is added if a Scode ends with a question mark.
        self.assertEqual(self.label_for_code('S4?'),
            'fairly widespread (uncertain)')


class EndangermentCodeLabelTests(TemplateTagTestCase):

    def label_for_code(self, code):
        template = (
            '{{% load taxa_tags %}}'
            '{{% endangerment_code_label "{code}" %}}'
        ).format(code=code)
        return self.render_template(template)

    def test_endangerment_code_h(self):
        self.assertEqual(self.label_for_code('- H'), 'historical')

    def test_endangerment_code_wl(self):
        self.assertEqual(self.label_for_code('- WL'), 'Watch List')

    def test_endangerment_code_c(self):
        self.assertEqual(self.label_for_code('C'), 'concern')

    def test_endangerment_code_c_star(self):
        self.assertEqual(self.label_for_code('C*'), 'concern (uncertain)')

    def test_endangerment_code_e(self):
        self.assertEqual(self.label_for_code('E'), 'endangered')

    def test_endangerment_code_fe(self):
        self.assertEqual(self.label_for_code('FE'), 'federally endangered')

    def test_endangerment_code_ft(self):
        self.assertEqual(self.label_for_code('FT'), 'federally threatened')

    def test_endangerment_code_ft_sh(self):
        self.assertEqual(self.label_for_code('FT/SH'),
            'federally threatened/state historical')

    def test_endangerment_code_pe(self):
        self.assertEqual(self.label_for_code('PE'), 'potentially extirpated')

    def test_endangerment_code_sc(self):
        self.assertEqual(self.label_for_code('SC'), 'special concern')

    def test_endangerment_code_sc_star(self):
        self.assertEqual(self.label_for_code('SC*'),
            'special concern, extirpated')

    def test_endangerment_code_se(self):
        self.assertEqual(self.label_for_code('SE'), 'state endangered')

    def test_endangerment_code_sh(self):
        self.assertEqual(self.label_for_code('SH'), 'state historical')

    def test_endangerment_code_sr(self):
        self.assertEqual(self.label_for_code('SR'), 'state rare')

    def test_endangerment_code_st(self):
        self.assertEqual(self.label_for_code('ST'), 'state threatened')

    def test_endangerment_code_t(self):
        self.assertEqual(self.label_for_code('T'), 'threatened')

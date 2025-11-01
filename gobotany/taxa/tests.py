# -*- coding: utf-8 -*-
"""Tests for the taxa (family, genus, and species) pages."""

import re
import unittest

from django.template import Context, Template
from django.test import TestCase

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

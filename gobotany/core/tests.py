# coding=windows-1252

import doctest
import os
import re
import unittest

from django.db import connection
from django.forms import ValidationError
from django.test import TestCase

from StringIO import StringIO

import bulkup
from gobotany.core import botany, igdt, importer, models

def testdata(s):
    """Return the path to a test data file relative to this directory."""
    return os.path.join(os.path.dirname(__file__), 'testdata', s)


class SampleData(TestCase):

    def create(self, type_, name, **kw):
        """Create an object and save it as ``self.<name>``."""
        if issubclass(type_, models.Taxon):
            kw['scientific_name'] = kw['genus'].name + ' ' + name
        elif issubclass(type_, models.Character):
            kw['short_name'] = name
        elif issubclass(type_, models.CharacterValue):
            kw['value_str'] = name
        else:
            kw['name'] = name
        obj = type_(**kw)
        obj.save()
        setattr(self, name.lower().replace(' ', '_'), obj)
        return obj

    def setup_sample_data(self):
        self.create(models.PileGroup, 'pilegroup1')
        self.assertEqual(self.pilegroup1.slug, 'pilegroup1')
        self.create(models.PileGroup, 'pilegroup2', slug='pilegroup2')

        self.create(models.Pile, 'Carnivores', pilegroup=self.pilegroup1)
        self.create(models.Pile, 'Pets', pilegroup=self.pilegroup1)

        self.create(models.Family, 'Canidae')
        self.create(models.Family, 'Felidae')
        self.create(models.Family, 'Leporidae')

        self.create(models.Genus, 'Vulpes', family=self.canidae)
        self.create(models.Genus, 'Felis', family=self.felidae)
        self.create(models.Genus, 'Oryctolagus', family=self.leporidae)

        self.create(models.Taxon, 'fox', family=self.canidae, genus=self.vulpes)
        self.create(models.Taxon, 'cat', family=self.felidae, genus=self.felis)
        self.create(models.Taxon, 'rabbit',
                    family=self.leporidae, genus=self.oryctolagus)

        self.carnivores.species.add(self.fox)
        self.carnivores.species.add(self.cat)
        self.pets.species.add(self.cat)
        self.pets.species.add(self.rabbit)

        self.create(models.CharacterGroup, 'appearance')
        self.create(models.CharacterGroup, 'dimensions')

        self.create(models.Character, 'color', friendly_name='What color?',
                    character_group=self.appearance, value_type=u'TEXT')
        self.create(models.Character, 'cuteness',
                    character_group=self.appearance, value_type=u'TEXT')
        self.create(models.Character, 'length',
                    character_group=self.dimensions, value_type=u'LENGTH')

        def make_cv(name, **kw):
            cv = self.create(models.CharacterValue, name, **kw)
            self.pets.character_values.add(cv)

        make_cv('red', character=self.color)
        make_cv('orange', character=self.color)
        make_cv('gray', character=self.color)
        make_cv('chartreuse', character=self.color)

        make_cv('cute', character=self.cuteness)

        make_cv('size1', character=self.length, value_min=2, value_max=4)
        make_cv('size2', character=self.length, value_min=3, value_max=4)
        make_cv('size3', character=self.length, value_min=5, value_max=5)

        self.create(models.ImageType, 'habit')
        self.create(models.ImageType, 'stem')
        self.create(models.ImageType, 'pile image')

        for taxon, cv in ((self.fox, self.red),
                          (self.fox, self.size3),
                          (self.cat, self.orange),
                          (self.cat, self.gray),
                          (self.cat, self.cute),
                          (self.cat, self.size2),
                          (self.rabbit, self.gray),
                          (self.rabbit, self.cute),
                          (self.rabbit, self.size1),
                          ):
            tcv = models.TaxonCharacterValue(taxon=taxon, character_value=cv)
            tcv.save()
        self.tcv = tcv  # saves the last one, for use by a test below


class SimpleTests(TestCase):

    def test_environment(self):
        self.assert_(True)


class ModelTests(SampleData):
    # Various tests to make sure models work well.

    def setUp(self):
        self.setup_sample_data()

    def do_unicode(self, obj, expected):
        actual = re.sub(r'id=\d+', 'id=x', unicode(obj))
        self.assertEqual(expected, actual)

    # Make sure each model has a reasonable Unicode representation.

    def test_PileGroup_unicode(self):
        self.do_unicode(self.pilegroup1, u'pilegroup1 id=x')

    def test_Pile_unicode(self):
        self.do_unicode(self.pets, u'Pets id=x')

    def test_CharacterGroup_unicode(self):
        self.do_unicode(self.appearance, u'appearance id=x')

    def test_numeric_CharacterValue_unicode(self):
        self.do_unicode(self.size1, u'length: 2 - 4')

    def test_ImageType_unicode(self):
        self.do_unicode(models.ImageType(name='my imagetype'), u'my imagetype')

    def test_ContentImage_unicode(self):
        leaf = models.ImageType(name='leaf')
        leaf.save()

        taxon = models.ContentType.objects.get(name='taxon')
        pile = models.ContentType.objects.get(name='pile')

        ci = models.ContentImage(alt='alttext', rank=3, image_type=leaf,
                                 content_type=taxon, object_id=self.cat.id)
        ci.save()
        self.do_unicode(ci, u'"alttext" - leaf image for Felis cat 3: ')

        ci = models.ContentImage(alt='alttext', rank=3, image_type=leaf,
                                 content_type=pile, object_id=self.pets.id)
        ci.save()
        self.do_unicode(ci, u'"alttext" - leaf image for pile: %d 3: '
                        % self.pets.id)

    def test_TaxonCharacterValue_unicode(self):
        self.do_unicode(self.tcv, u'Oryctolagus rabbit: length: 2 - 4')

    def test_DefaultFilter_unicode(self):
        defaultfilter1 = models.DefaultFilter()
        defaultfilter1.pile = self.carnivores
        defaultfilter1.character = self.color
        defaultfilter1.order = 7
        defaultfilter1.save()

        self.do_unicode(defaultfilter1, u'Carnivores default #7: What color?')

    def test_PlantPreviewCharacter_unicode(self):
        plantpreview = models.PlantPreviewCharacter()
        plantpreview.pile = self.carnivores
        plantpreview.character = self.color
        plantpreview.order = 7
        plantpreview.save()

        self.do_unicode(plantpreview, u'7: What color? (Carnivores)')

    def test_CharacterValue_value_with_float(self):
        cv = models.CharacterValue()
        cv.value_flt = 1.9
        self.assertEqual(cv.value, 1.9)

    def test_CharacterValue_value_with_range(self):
        cv = models.CharacterValue()
        cv.value_min = 1
        cv.value_max = 9
        self.assertEqual(cv.value, (1, 9))

    def test_CharacterValue_value_with_string(self):
        cv = models.CharacterValue()
        cv.value_str = 'test value'
        self.assertEqual(cv.value, 'test value')

    # Exercise cleanup routines that come with some models.

    def test_CharacterValue_clean(self):
        CV = models.CharacterValue
        raises = self.assertRaises

        cv = CV(value_str = '')
        cv.clean()
        assert cv.value_str is None

        CV(value_str='a').clean()
        CV(value_flt=1.1).clean()
        CV(value_min=5, value_max=7).clean()

        raises(ValidationError, CV(value_str='a', value_max=3).clean)
        raises(ValidationError, CV(value_str='a', value_flt='a').clean)
        raises(ValidationError, CV(value_flt=3.2, value_min=2).clean)

        raises(ValidationError, CV(value_min=2).clean)
        raises(ValidationError, CV(value_max=3).clean)
        raises(ValidationError, CV(value_min=200, value_max=3).clean)

    def test_ContentImage_clean(self):
        taxon = models.ContentType.objects.get(name='taxon')

        CI = models.ContentImage
        kw = dict(image_type=self.stem, content_type=taxon, object_id='1')
        ci1 = CI(rank=1, **kw)
        ci1.save()  # no complaint
        ci2 = CI(rank=2, **kw)
        ci2.save()  # no complaint
        ci3 = CI(rank=2, **kw)
        ci3.save()  # no complaint
        ci4 = CI(rank=1, **kw)
        self.assertRaises(ValidationError, ci4.save)  # already a rank=1

    # Test some other miscellaneous methods.

    def test_Taxon_get_piles(self):
        self.assertEqual(self.cat.get_piles(), [u'Carnivores', u'Pets'])

    def test_Pile_get_default_image(self):
        pile = models.ContentType.objects.get(name='pile')

        CI = models.ContentImage
        kw = dict(content_type=pile, object_id=self.pets.id)

        self.assertEqual(self.pets.get_default_image(), None)

        ci1 = CI(rank=2, image_type=self.stem, **kw)
        ci1.save()
        self.assertEqual(self.pets.get_default_image(), None)
        ci2 = CI(rank=1, image_type=self.stem, **kw)
        ci2.save()
        self.assertEqual(self.pets.get_default_image(), None)

        ci3 = CI(rank=2, image_type=self.pile_image, **kw)
        ci3.save()
        self.assertEqual(self.pets.get_default_image(), None)
        ci4 = CI(rank=1, image_type=self.pile_image, **kw)
        ci4.save()
        self.assertEqual(self.pets.get_default_image(), ci4)

    def test_Taxon_get_default_image(self):
        taxon = models.ContentType.objects.get(name='taxon')

        CI = models.ContentImage
        kw = dict(content_type=taxon, object_id=self.cat.id)

        self.assertEqual(self.cat.get_default_image(), None)

        ci1 = CI(rank=2, image_type=self.stem, **kw)
        ci1.save()
        self.assertEqual(self.cat.get_default_image(), None)
        ci2 = CI(rank=1, image_type=self.stem, **kw)
        ci2.save()
        self.assertEqual(self.cat.get_default_image(), None)

        ci3 = CI(rank=2, image_type=self.habit, **kw)
        ci3.save()
        self.assertEqual(self.cat.get_default_image(), None)
        ci4 = CI(rank=1, image_type=self.habit, **kw)
        ci4.save()
        self.assertEqual(self.cat.get_default_image(), ci4)


class APITests(SampleData):
    # Tests of the Python API, that make manual Python function calls
    # without an intervening layer of Django URLs and views.

    def setUp(self):
        self.setup_sample_data()

    def try_query(self, result, *args, **kw):
        result_set = set(result)
        real_result_set = set(botany.query_species(*args, **kw))
        self.assertEqual(result_set, real_result_set)

    def test_query_unknown_character(self):
        self.assertRaises(models.Character.DoesNotExist,
                          self.try_query, [], bad_character='red')

    def test_query_species(self):
        queried = botany.query_species(scientific_name='Felis cat').all()
        self.assert_(len(queried) == 1)

        self.try_query([self.fox], color='red')
        self.try_query([self.cat, self.rabbit], color='gray')
        self.try_query([], color='chartreuse')

        self.try_query([self.fox, self.cat], pile='carnivores')
        self.try_query([self.cat, self.rabbit], pile='pets')
        self.try_query([self.fox], pile='carnivores', color='red')
        self.try_query([], pile='carnivores', color='chartreuse')

        self.try_query([self.fox, self.cat, self.rabbit],
                       pilegroup='pilegroup1')
        self.try_query([], pilegroup='pilegroup2')
        self.try_query([self.cat], pilegroup='pilegroup1', color='orange')
        self.try_query([], pilegroup='pilegroup2', color='orange')

        self.try_query([self.fox, self.cat],
                       pile='carnivores', pilegroup='pilegroup1')
        self.try_query([], pile='carnivores', pilegroup='pilegroup2')

        self.try_query([self.cat], genus='Felis')
        self.try_query([self.fox], family='Canidae')
        self.try_query([], genus='Kooky')

    def test_query_length(self):
        self.try_query([], length=1)
        self.try_query([self.rabbit], length=2)
        self.try_query([self.cat, self.rabbit], length=3)
        self.try_query([self.cat, self.rabbit], length=4)
        self.try_query([self.fox], length=5)
        self.try_query([], length=6)

    def test_species_images(self):
        taxon = models.ContentType.objects.get(name='taxon')
        CI = models.ContentImage
        species_images = botany.species_images

        # Create several images.

        for i in ('fox_habit_1', 'fox_habit_2', 'fox_habit_3', 'fox_habit_11',
                  'fox_stem_2', 'fox_stem_4',
                  'cat_habit_1', 'cat_stem_2',
                  ):
            species_spec, image_type_spec, rank = i.split('_')
            species = getattr(self, species_spec)
            image_type = getattr(self, image_type_spec)
            ci = CI(rank=rank, image_type=image_type,
                    content_type=taxon, object_id=species.id)
            ci.save()
            exec '%s = ci' % i

        # Try fetching some images.

        self.assertEqual(
            set(species_images(self.fox)),
            set([fox_habit_1, fox_habit_2, fox_habit_3,
                 fox_stem_2, fox_stem_4]))

        self.assertEqual(
            set(species_images(self.fox, image_types=[self.habit])),
            set([fox_habit_1, fox_habit_2, fox_habit_3]))

        self.assertEqual(
            set(species_images(self.fox, max_rank=2)),
            set([fox_habit_1, fox_habit_2, fox_stem_2]))

        self.assertEqual(
            set(species_images(self.fox, image_types='stem', max_rank=3)),
            set([fox_stem_2]))

        self.assertEqual(
            set(species_images(self.fox, image_types='stem', max_rank=3)),
            set([fox_stem_2]))

        self.assertEqual(
            set(species_images('Vulpes fox', image_types='stem', max_rank=3)),
            set([fox_stem_2]))

    def test_best_filters(self):
        celist = igdt.compute_character_entropies(
            self.carnivores, list(models.Taxon.objects.all()))
        self.assertEqual(celist, [])

        celist = igdt.compute_character_entropies(
            self.pets, list(models.Taxon.objects.all()))
        self.assertEqual(sorted(celist), [
                (self.color.id, 0.66666666666666663, 1.0),
                (self.cuteness.id, 0.66666666666666663, 0.66666666666666663),
                (self.length.id, 0.0, 1.0),
                ])


class ImportTestCase(TestCase):
    def setUp(self):
        self.db = bulkup.Database(connection)

    def test_character_short_name_retains_pile_suffix(self):
        im = importer.Importer()
        short_name = im.character_short_name('this_is_a_character_ly')
        self.assertEquals('this_is_a_character_ly', short_name)

    def test_character_short_name_removes_min(self):
        im = importer.Importer()
        short_name = im.character_short_name('this_is_a_length_char_min_ly')
        self.assertEquals('this_is_a_length_char_ly', short_name)

    def test_character_short_name_removes_max(self):
        im = importer.Importer()
        short_name = im.character_short_name('this_is_a_length_char_max_ly')
        self.assertEquals('this_is_a_length_char_ly', short_name)

    def test_import_characters(self):
        im = importer.Importer()
        im._import_characters(self.db, testdata('characters.csv'))
        f = open(testdata('characters.csv'))
        content = f.read()
        f.close()
        expected = len(content.splitlines()) - min(content.count('_min'),
                                                   content.count('_max')) - 1
        self.assertEquals(len(models.Character.objects.all()), expected)

    def test_import_taxons(self):
        im = importer.Importer()
        im._import_partner_sites(self.db)
        im._import_pile_groups(self.db, testdata('pile_group_info.csv'))
        im._import_piles(self.db, testdata('pile_info.csv'))
        im._import_taxa(self.db, testdata('taxa.csv'))
        self.assertEquals(len(models.Taxon.objects.all()), 3522)

    def test_clean_up_html_non_breaking_spaces(self):
        im = importer.Importer()
        self.assertEquals('Remove non-breaking spaces. Please.',
            im._clean_up_html('Remove non-breaking spaces. &nbsp;Please.'))

    def test_clean_up_html_font_tags(self):
        im = importer.Importer()
        html = ('<div><font color=""#333333"">non-grasses have very narrow '
                'leaves, but produce showy flowers</font></div>')
        expected = ('<div>non-grasses have very narrow leaves, but produce '
                    'showy flowers</div>')
        self.assertEquals(expected, im._clean_up_html(html))

    def test_has_unexpected_delimiter(self):
        im = importer.Importer()
        text = 'This, has, no, unexpected, delimiter'
        self.assertFalse(im._has_unexpected_delimiter(text,
                        unexpected_delimiter='|'))
        text = 'This|has|an|unexpected|delimiter'
        self.assertTrue(im._has_unexpected_delimiter(text,
                         unexpected_delimiter='|'))

    def test_create_character_name(self):
        im = importer.Importer()
        name = im._create_character_name('stamen_morphology')
        self.assertEqual('Stamen morphology', name)

    def test_get_character_friendly_name(self):
        im = importer.Importer()
        friendly_name = im._get_character_friendly_name( \
            'spike_number_per_stem', 'Number of spikes')
        self.assertEqual('Number of spikes', friendly_name)

    def test_get_character_friendly_name_not_defined(self):
        im = importer.Importer()
        friendly_name = im._get_character_friendly_name('plant_habit', '')
        self.assertEqual('Plant habit', friendly_name)
        friendly_name = im._get_character_friendly_name('leaf_disposition',
            None)
        self.assertEqual('Leaf disposition', friendly_name)


class StateStatusTestCase(TestCase):

    DISTRIBUTION = ['MA', 'VT']

    def test_get_state_status_is_present(self):
        im = importer.Importer()
        status = im._get_state_status('MA', self.DISTRIBUTION)
        self.assertEqual('present', status)

    def test_get_state_status_is_absent(self):
        im = importer.Importer()
        status = im._get_state_status('CT', self.DISTRIBUTION)
        self.assertEqual('absent', status)

    def test_get_state_status_is_absent_and_has_conservation_status(self):
        # Exclude extinct status ('X') from this list; it is an exception
        # and has its own test.
        im = importer.Importer()
        status_codes = ['E', 'T', 'SC', 'SC*', 'H', 'C']
        for status_code in status_codes:
            status = im._get_state_status('CT', self.DISTRIBUTION,
                conservation_status_code=status_code)
            self.assertEqual('absent', status)

    def test_get_state_status_is_endangered(self):
        im = importer.Importer()
        status = im._get_state_status('MA', self.DISTRIBUTION,
                                      conservation_status_code='E')
        self.assertEqual('present, endangered', status)

    def test_get_state_status_is_threatened(self):
        im = importer.Importer()
        status = im._get_state_status('MA', self.DISTRIBUTION,
                                      conservation_status_code='T')
        self.assertEqual('present, threatened', status)

    def test_get_state_status_has_special_concern(self):
        im = importer.Importer()
        status_codes = ['SC', 'SC*']
        for status_code in status_codes:
            status = im._get_state_status('MA', self.DISTRIBUTION,
                conservation_status_code=status_code)
            self.assertEqual('present, special concern', status)

    def test_get_state_status_is_historic(self):
        im = importer.Importer()
        status = im._get_state_status('MA', self.DISTRIBUTION,
                                      conservation_status_code='H')
        self.assertEqual('present, historic', status)

    def test_get_state_status_is_extinct(self):
        im = importer.Importer()
        status = im._get_state_status('ME', self.DISTRIBUTION,
                                      conservation_status_code='X')
        self.assertEqual('extinct', status)
        # Extinct should appear alone even if the plant is marked present.
        status = im._get_state_status('MA', self.DISTRIBUTION,
                                      conservation_status_code='X')
        self.assertEqual('extinct', status)

    def test_get_state_status_is_rare(self):
        im = importer.Importer()
        status = im._get_state_status('MA', self.DISTRIBUTION,
                                      conservation_status_code='C')
        self.assertEqual('present, rare', status)

    def test_get_state_status_is_invasive(self):
        im = importer.Importer()
        status = im._get_state_status('MA', self.DISTRIBUTION,
                                      is_invasive=True)
        self.assertEqual('present, invasive', status)

    def test_get_state_status_is_invasive_and_prohibited(self):
        im = importer.Importer()
        status = im._get_state_status('MA', self.DISTRIBUTION,
                                      is_invasive=True,
                                      is_prohibited=True)
        self.assertEqual('present, invasive, prohibited', status)

    def test_get_state_status_is_absent_and_prohibited(self):
        im = importer.Importer()
        status = im._get_state_status('ME', self.DISTRIBUTION,
                                      is_prohibited=True)
        self.assertEqual('absent, prohibited', status)


class StripTaxonomicAuthorityTestCase(TestCase):

    def test_strip_taxonomic_authority_species(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority('Viburnum cassanoides L.')
        self.assertEqual('Viburnum cassanoides', name)

    def test_strip_taxonomic_authority_species_extra_punctuation(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Actaea alba, of authors not (L.) P. Mill.')
        self.assertEqual('Actaea alba', name)

    def test_strip_taxonomic_authority_subspecies(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Lysimachia lanceolata subsp. hybrida (Michx.) J.D. Ray')
        self.assertEqual('Lysimachia lanceolata subsp. hybrida', name)
        # Test alternate connector.
        name = im._strip_taxonomic_authority( \
            'Lysimachia lanceolata ssp. hybrida (Michx.) J.D. Ray')
        self.assertEqual('Lysimachia lanceolata ssp. hybrida', name)

    def test_strip_taxonomic_authority_variety(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Vitis labrusca var. subedentata Fern.')
        self.assertEqual('Vitis labrusca var. subedentata', name)

    def test_strip_taxonomic_authority_subvariety(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Potentilla anserina subvar. minima (Peterm. ex Th.Wolf) Th.Wolf')
        self.assertEqual('Potentilla anserina subvar. minima', name)

    def test_strip_taxonomic_authority_forma(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            ('Acanthocalycium spiniflorum f. klimpelianum (Weidlich & '
             'Werderm.) Donald'))
        self.assertEqual('Acanthocalycium spiniflorum f. klimpelianum', name)
        # Test alternate connector.
        name = im._strip_taxonomic_authority( \
            ('Acanthocalycium spiniflorum forma klimpelianum (Weidlich & '
             'Werderm.) Donald'))
        self.assertEqual('Acanthocalycium spiniflorum forma klimpelianum',
                         name)

    def test_strip_taxonomic_authority_subforma(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Saxifraga aizoon subf. surculosa Engl. & Irmsch.')
        self.assertEqual('Saxifraga aizoon subf. surculosa', name)

    def test_strip_taxonomic_authority_infraspecific_epithet_later(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Actaea spicata L. ssp. rubra (Ait.) Hulten')
        self.assertEqual('Actaea spicata ssp. rubra', name)
        # Test another connector, with the epithet coming even later.
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Gerardia paupercula (Gray) Britt. var. typica Pennell')
        self.assertEqual('Gerardia paupercula var. typica', name)

    def test_strip_taxonomic_authority_skip_consecutive_connector(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority( \
            'Betula lutea Michx. f. var. fallax Fassett')
        self.assertEqual('Betula lutea var. fallax', name)

    def test_strip_taxonomic_authority_no_epithet_after_connector(self):
        im = importer.Importer()
        name = im._strip_taxonomic_authority('Betula lutea Michx. f.')
        self.assertEqual('Betula lutea', name)

    def test_strip_taxonomic_authority_unexpected_characters(self):
        im = importer.Importer()
        # This name has some undesirable character data in it (showing up as
        # a dagger here), as copied from the CSV. It is decoded here using
        # Windows-1252 like the importer does when reading CSV files (see
        # CSVReader read method override in importer.py).
        name_with_unexpected_characters = \
            'Cornus amomum var. schuetzeana†(C.A. Mey.) Rickett'.decode(
            'Windows-1252')
        name = im._strip_taxonomic_authority(name_with_unexpected_characters)
        self.assertEqual('Cornus amomum var. schuetzeana', name)

    def test_strip_taxonomic_authority_missing_space_after_epithet(self):
        im = importer.Importer()
        name_missing_space = 'Lycopodium annotinum var. montanumTuckerman'
        name = im._strip_taxonomic_authority(name_missing_space)
        self.assertEqual('Lycopodium annotinum var. montanum', name)
        # Sometimes there are parentheses instead of a capital letter.
        name_missing_space = 'Huperzia selago ssp. appressa(Desv.)'
        name = im._strip_taxonomic_authority(name_missing_space)
        self.assertEqual('Huperzia selago ssp. appressa', name)


def setup_integration(test):
    pilegroup1 = models.PileGroup(name='pilegroup1')
    pilegroup1.save()

    pile1 = models.Pile(name='Carex')
    pile1.pilegroup = pilegroup1
    pile1.save()

    im = importer.Importer()

    im._import_piles(testdata('pile_info.csv'), None)
    im._import_taxa(testdata('taxa.csv'))
    im._import_characters(testdata('characters.csv'))
    im._import_character_values(testdata('character_values.csv'))
    im._import_taxon_character_values(testdata('pile_lycophytes.csv'))
    im._import_taxon_character_values(
        testdata('pile_non_orchid_monocots_1.csv'))
    im._import_taxon_character_values(
        testdata('pile_non_orchid_monocots_2.csv'))
    im._import_taxon_character_values(
        testdata('pile_non_orchid_monocots_3.csv'))


def test_class_iter():
    m = __import__(__name__, {}, {}, __name__)
    for x in dir(m):
        i = getattr(m, x)
        if type(i) == type and issubclass(i, TestCase):
            yield i


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(igdt))
    for x in test_class_iter():
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(x))

    # integration stuff - turned off for the moment since the test
    #   is both broken, and takes a long time to run
    # suite.addTest(doctest.DocFileSuite('igdt.txt',
    #                                    module_relative=True,
    #                                    setUp=setup_integration))

    return suite

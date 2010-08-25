import doctest
import os
import re
import unittest
from StringIO import StringIO
from django.forms import ValidationError 
from django.test import TestCase
from gobotany.core import botany
from gobotany.core import models
from gobotany.core import igdt
from gobotany.core import importer


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

    def setup_sample_data(self):
        self.create(models.PileGroup, 'pilegroup1')
        self.create(models.PileGroup, 'pilegroup2')

        self.create(models.Pile, 'Carnivores', pilegroup=self.pilegroup1)
        self.create(models.Pile, 'Pets', pilegroup=self.pilegroup1)

        self.create(models.Family, 'Canidae')
        self.create(models.Family, 'Felidae')
        self.create(models.Family, 'Leporidae')

        self.create(models.Genus, 'Vulpes')
        self.create(models.Genus, 'Felis')
        self.create(models.Genus, 'Oryctolagus')

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

        self.create(models.CharacterValue, 'red', character=self.color)
        self.create(models.CharacterValue, 'orange', character=self.color)
        self.create(models.CharacterValue, 'gray', character=self.color)
        self.create(models.CharacterValue, 'chartreuse', character=self.color)

        self.create(models.CharacterValue, 'cute', character=self.cuteness)

        self.create(models.CharacterValue, 'size1',character=self.length,
                    value_min=2, value_max=4)
        self.create(models.CharacterValue, 'size2', character=self.length,
                    value_min=3, value_max=4)
        self.create(models.CharacterValue, 'size3',character=self.length,
                    value_min=5, value_max=5)

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
        self.do_unicode(self.tcv, u'length: 2 - 4')

    def test_TaxonGroup_unicode(self):
        self.create(models.TaxonGroup, 'taxongroup1')

        taxongroupentry1 = models.TaxonGroupEntry()
        taxongroupentry1.taxon = self.cat
        taxongroupentry1.group = self.taxongroup1
        taxongroupentry1.save()

        self.do_unicode(self.taxongroup1, u'taxongroup1')
        self.do_unicode(taxongroupentry1, u'taxongroup1: Felis cat')

    def test_DefaultFilter_unicode(self):
        defaultfilter1 = models.DefaultFilter()
        defaultfilter1.pile = self.carnivores
        defaultfilter1.character = self.color
        defaultfilter1.order = 7
        defaultfilter1.save()

        self.do_unicode(defaultfilter1, u'7: What color? (Carnivores)')

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

class ImportTestCase(TestCase):

    def test_import_characters(self):
        im = importer.Importer(StringIO())
        im._import_characters(testdata('characters.csv'))
        f = open(testdata('characters.csv'))
        content = f.read()
        f.close()
        expected = len(content.splitlines()) - content.count('_max') - 1
        self.assertEquals(len(models.Character.objects.all()), expected)

    def test_import_taxons(self):
        im = importer.Importer(StringIO())
        im._import_taxa(testdata('taxa.csv'))
        self.assertEquals(len(models.Taxon.objects.all()), 71)


def setup_integration(test):
    pilegroup1 = models.PileGroup(name='pilegroup1')
    pilegroup1.save()

    pile1 = models.Pile(name='Carex')
    pile1.pilegroup = pilegroup1
    pile1.save()

    im = importer.Importer(StringIO())

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

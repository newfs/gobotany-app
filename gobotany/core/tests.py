import doctest
import os
import unittest
from StringIO import StringIO
from django.test import TestCase
from gobotany.core import botany
from gobotany.core import models
from gobotany.core import igdt
from gobotany.core import importer
from gobotany.api import handlers  # TODO: move some tests to "api" package?


def testdata(s):
    """Return the path to a test data file relative to this directory."""
    return os.path.join(os.path.dirname(__file__), 'testdata', s)


class SampleDataTestCase(TestCase):

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
        setattr(self, name.lower(), obj)

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

        self.create(models.Character, 'color',
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
            models.TaxonCharacterValue(taxon=taxon, character_value=cv).save()


class SimpleTests(TestCase):

    def test_environment(self):
        self.assert_(True)


class APITests(SampleDataTestCase):
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


# class RESTFulTests(SampleDataTestCase):

#     def test_taxon_with_chars(self):
#         self.setup_sample_data()
#         foo = models.Taxon.objects.get(scientific_name='Foo foo')
#         handlers._taxon_with_chars(foo)


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

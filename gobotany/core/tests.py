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


def setup_sample_data():
    pilegroup1 = models.PileGroup(name='pilegroup1')
    pilegroup1.save()
    pilegroup2 = models.PileGroup(name='pilegroup2')
    pilegroup2.save()

    pile1 = models.Pile(name='pile1')
    pile1.pilegroup = pilegroup1
    pile1.save()
    pile2 = models.Pile(name='pile2')
    pile2.pilegroup = pilegroup2
    pile2.save()

    famfoo, c = models.Family.objects.get_or_create(name='Fooaceae')
    fambaz, c = models.Family.objects.get_or_create(name='Bazaceae')

    genfoo, c = models.Genus.objects.get_or_create(name='Fooium')
    genbaz, c = models.Genus.objects.get_or_create(name='Bazia')

    foo = models.Taxon(family=famfoo, genus=genfoo, scientific_name='Foo foo')
    foo.save()
    bar = models.Taxon(family=famfoo, genus=genfoo, scientific_name='Foo bar')
    bar.save()
    abc = models.Taxon(family=fambaz, genus=genbaz, scientific_name='Baz abc')
    abc.save()

    pile1.species.add(foo)
    pile1.species.add(bar)
    pile1.species.add(abc)

    cg1 = models.CharacterGroup(name='cg1')
    cg1.save()

    c1 = models.Character(short_name='c1', character_group=cg1)
    c1.save()
    c2 = models.Character(short_name='c2', character_group=cg1)
    c2.save()

    cv1 = models.CharacterValue(value_str='cv1',
                                character=c1)
    cv1.save()
    cv2 = models.CharacterValue(value_str='cv2',
                                character=c1)
    cv2.save()

    pile1.character_values.add(cv1)
    pile1.character_values.add(cv2)
    pile1.save()

    models.TaxonCharacterValue(taxon=foo, character_value=cv1).save()
    models.TaxonCharacterValue(taxon=bar, character_value=cv2).save()


class SimpleTests(TestCase):

    def test_environment(self):
        self.assert_(True)


class APITests(TestCase):

    def setUp(self):
        setup_sample_data()

    def try_query(self, result, *args, **kw):
        result_set = set(result)
        real_result_set = set(botany.query_species(*args, **kw))
        self.assertEqual(result_set, real_result_set)

    def test_query_species(self):
        queried = botany.query_species(scientific_name='Foo foo').all()
        self.assert_(len(queried) == 1)

        foo = models.Taxon.objects.filter(scientific_name='Foo foo')[0]
        bar = models.Taxon.objects.filter(scientific_name='Foo bar')[0]
        abc = models.Taxon.objects.filter(scientific_name='Baz abc')[0]

        self.try_query([foo], c1='cv1')
        self.try_query([bar], c1='cv2')

        self.try_query([foo, bar, abc], pile='pile1')
        self.try_query([], pile='pile2')
        self.try_query([foo], pile='pile1', c1='cv1')
        self.try_query([], pile='pile2', c1='cv1')

        self.try_query([foo, bar, abc], pilegroup='pilegroup1')
        self.try_query([], pilegroup='pilegroup2')
        self.try_query([foo], pilegroup='pilegroup1', c1='cv1')
        self.try_query([], pilegroup='pilegroup2', c1='cv1')

        self.try_query([foo, bar, abc], pile='pile1', pilegroup='pilegroup1')
        self.try_query([], pile='pile2', pilegroup='pilegroup1')

        self.try_query([foo, bar], genus='Fooium')
        self.try_query([abc], family='Bazaceae')
        self.try_query([], genus='Kooky')


class ImportTests(TestCase):

    def test_import_characters(self):
        im = importer.Importer(StringIO())
        im._import_characters(os.path.join(os.path.dirname(__file__),
                                           'test_characters.csv'))
        self.assertEquals(len(models.Character.objects.all()), 4)

    def test_import_taxons(self):
        # setup the Carex pile for the test char data

        pilegroup1 = models.PileGroup(name='pilegroup1')
        pilegroup1.save()

        pile1 = models.Pile(name='Carex')
        pile1.pilegroup = pilegroup1
        pile1.save()

        im = importer.Importer(StringIO())
        im._import_characters(os.path.join(os.path.dirname(__file__),
                                           'test_characters.csv'))
        im._import_taxon_character_values(
            os.path.join(os.path.dirname(__file__),
                         'test_taxons.csv'))
        # The number of taxa created should be zero, since the method
        # _import_taxon_character_values() no longer lazily creates taxa
        # that have not already been created.
        self.assertEquals(len(models.Taxon.objects.all()), 0)


class RESTFulTests(TestCase):

    def test_taxon_with_chars(self):
        setup_sample_data()
        foo = models.Taxon.objects.get(scientific_name='Foo foo')
        handlers._taxon_with_chars(foo)


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
    return suite

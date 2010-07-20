import os
from StringIO import StringIO
from django.test import TestCase
from gobotany import botany
from gobotany import models
from gobotany import importer
from gobotany import handlers


def setup_sample_data():
    pile = models.Pile(name='pile1')
    pile.save()

    foo = models.Taxon(scientific_name='foo')
    foo.save()
    bar = models.Taxon(scientific_name='bar')
    bar.save()
    abc = models.Taxon(scientific_name='abc')
    abc.save()

    pile.species.add(foo)
    pile.species.add(bar)
    pile.species.add(abc)

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

    pile.character_values.add(cv1)
    pile.character_values.add(cv2)
    pile.save()

    models.TaxonCharacterValue(taxon=foo, character_value=cv1).save()
    models.TaxonCharacterValue(taxon=bar, character_value=cv2).save()


class SimpleTests(TestCase):

    def test_environment(self):
        self.assert_(True)


class APITests(TestCase):

    def setUp(self):
        setup_sample_data()

    def test_query_species(self):
        queried = botany.query_species(scientific_name='foo').all()
        self.assert_(len(queried) == 1)

        foo = models.Taxon.objects.filter(scientific_name='foo')[0]
        bar = models.Taxon.objects.filter(scientific_name='bar')[0]

        self.assertEqual(list(botany.query_species(c1='cv1')), [foo])
        self.assertEqual(list(botany.query_species(c1='cv2')), [bar])


class ImportTests(TestCase):

    def test_import_characters(self):
        im = importer.Importer(StringIO())
        im._import_characters(os.path.join(os.path.dirname(__file__),
                                           'test_characters.csv'))
        self.assertEquals(len(models.Character.objects.all()), 4)
        self.assertEquals(len(models.CharacterValue.objects.all()), 8)

    def test_import_taxons(self):
        im = importer.Importer(StringIO())
        im._import_characters(os.path.join(os.path.dirname(__file__),
                                           'test_characters.csv'))
        im._import_taxons(os.path.join(os.path.dirname(__file__),
                                       'test_taxons.csv'))
        self.assertEquals(len(models.Taxon.objects.all()), 2)


class RESTFulTests(TestCase):

    def test_taxon_with_chars(self):
        setup_sample_data()
        foo = models.Taxon.objects.get(scientific_name='foo')
        handlers._taxon_with_chars(foo)

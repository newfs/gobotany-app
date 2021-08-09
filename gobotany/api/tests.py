import json
import logging
import os
import shutil

from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.test import TestCase
from django.test.client import Client

from gobotany.core import models

def _testdata_dir():
    """Return the path to a test data directory relative to this directory."""
    return os.path.join(os.path.dirname(__file__), 'testdata')

def _setup_sample_data(load_images=False):
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

    famfoo, created = models.Family.objects.get_or_create(name='Fooaceae')
    fambaz, created = models.Family.objects.get_or_create(name='Bazaceae')

    genfoo, created = models.Genus.objects.get_or_create(name='Fooium',
                      family=famfoo)
    genbaz, created = models.Genus.objects.get_or_create(name='Bazia',
                      family=fambaz)

    foo = models.Taxon(family=famfoo, genus=genfoo,
        scientific_name='Fooium fooia')
    foo.save()
    bar = models.Taxon(family=famfoo, genus=genfoo,
        scientific_name='Fooium barula')
    bar.save()
    abc = models.Taxon(family=fambaz, genus=genbaz,
        scientific_name='Bazia americana')
    abc.save()

    # Since loading the images slows things down, only load them if asked to.
    if load_images:
        image_type, c = models.ImageType.objects.get_or_create(name='taxon')
        content_type, c = ContentType.objects.get_or_create(
            model='', app_label='core')
        # Create one image.
        im1 = models.ContentImage(alt='im1 alt', rank=1,
            creator='photographer A', image_type=image_type,
            content_type=content_type, object_id=bar.id)
        filename = 'huperzia-appressa-ha-flastname-1.jpg'
        f = open('%s/%s' % (_testdata_dir(), filename), 'rb')
        image_file = File(f)
        im1.image.save(filename, image_file)
        im1.save()
        f.close()
        # Create another image.
        im2 = models.ContentImage(alt='im2 alt', rank=2,
            creator='photographer B', image_type=image_type,
            content_type=content_type, object_id=bar.id)
        filename = 'huperzia-appressa-ha-flastname-1.jpg'
        f = open('%s/%s' % (_testdata_dir(), filename), 'rb')
        image_file = File(f)
        im2.image.save(filename, image_file)
        im2.save()
        f.close()
        # Add the images to the taxon.
        bar.images.set([im1, im2])
        bar.save()

    pile1.species.add(foo)
    pile1.species.add(bar)
    pile1.species.add(abc)

    cg1 = models.CharacterGroup(name='cg1', id='1')
    cg1.save()

    c1 = models.Character(short_name='c1', name='Character 1',
                          character_group=cg1)
    c1.save()
    c2 = models.Character(short_name='c2', name='Character 2',
                          character_group=cg1)
    c2.save()
    c3 = models.Character(short_name='c3', name='Character 3',
                          character_group=cg1, value_type='LENGTH')
    c3.save()
    c4 = models.Character(short_name='c4', name='Character 4',
                          character_group=cg1)
    c4.save()
    char_habitat = models.Character(short_name='habitat', name='Habitat',
                                    character_group=cg1)
    char_habitat.save()

    cv1_1 = models.CharacterValue(value_str='cv1_1', character=c1)
    cv1_1.save()
    cv1_2 = models.CharacterValue(value_str='cv1_2', character=c1)
    cv1_2.save()
    cv2 = models.CharacterValue(value_str='cv2', character=c2)
    cv2.save()
    cv3 = models.CharacterValue(value_min=5, value_max=11, character=c3)
    cv3.save()
    cv_habitat1 = models.CharacterValue(value_str='forests',
        character=char_habitat)
    cv_habitat1.save()
    cv_habitat2 = models.CharacterValue(value_str='edges of forests',
        character=char_habitat)
    cv_habitat2.save()

    pile1.characters.add(c1)
    pile1.characters.add(c2)
    pile1.characters.add(c3)
    pile1.characters.add(char_habitat)
    pile1.save()

    models.TaxonCharacterValue(taxon=foo, character_value=cv1_1).save()
    models.TaxonCharacterValue(taxon=bar, character_value=cv1_2).save()
    models.TaxonCharacterValue(taxon=bar, character_value=cv2).save()
    models.TaxonCharacterValue(taxon=bar, character_value=cv_habitat1).save()
    models.TaxonCharacterValue(taxon=bar, character_value=cv_habitat2).save()

    # Create a couple of default filters here, making sure not to create
    # one for *every* character, so as to exercise some code in the
    # handlers that deals with a default filter not existing for a character.
    df1 = models.DefaultFilter(pile=pile1, character=c1, order=1)
    df1.save()

    df2 = models.DefaultFilter(pile=pile1, character=c2, order=2)
    df2.save()

    ppc1 = models.PlantPreviewCharacter(pile=pile1, character=c1, order=1)
    ppc1.save()

    ppc2 = models.PlantPreviewCharacter(pile=pile1, character=c2, order=2)
    ppc2.save()

    pile1.plant_preview_characters.members = [ppc1, ppc2]
    pile1.save()

def _remove_content_images_dir():
    """Remove a temporary content_images directory if it exists. This
    gets created when setting up the test data with the load_images=True,
    whereupon the setup code saves some ImageField objects. This function
    can be called from the tearDown method of a test class for cleanup.
    """
    content_images_path = os.path.join(os.getcwd(), 'content_images')
    if (os.path.isdir(content_images_path) and
        content_images_path.find('gobotany-deploy') > -1):
        shutil.rmtree(content_images_path)

# These two functions can be called from a test class's setUp and tearDown
# functions, respectively, to suppress Request Not Found warnings from calling
# known nonexistent URLs in tests.
def _setLoggingLevelError(self):
    # Change logging level to suppress Request Not Found warnings.
    self.logger = logging.getLogger('django.request')
    self.previous_level = self.logger.getEffectiveLevel()
    self.logger.setLevel(logging.ERROR)
def _restoreLoggingLevel(self):
    # Restore the previous logging level.
    self.logger.setLevel(self.previous_level)


class TaxaListTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_returns_ok(self):
        response = self.client.get('/api/taxa/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/taxa/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_with_char_param_returns_ok(self):
        response = self.client.get('/api/taxa/?c1=cv1_1')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_param_returns_not_found_if_no_char(self):
        response = self.client.get('/api/taxa/?none=cv1_1')
        self.assertEqual(404, response.status_code)

    def test_get_with_char_param_returns_ok_if_bad_char_value(self):
        response = self.client.get('/api/taxa/?c1=badvalue')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_param_returns_no_items_if_bad_char_value(self):
        response = self.client.get('/api/taxa/?c1=badvalue')
        expected = {'items': [],
                    'identifier': 'scientific_name',
                    'label': 'scientific_name'}
        self.assertEqual(expected, json.loads(response.content))


class TaxaTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_returns_ok(self):
        response = self.client.get('/api/taxa/Fooium%20barula/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/taxa/Fooium%20barula/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_species(self):
        response = self.client.get('/api/taxa/Not%20here/')
        self.assertEqual(404, response.status_code)

    # TODO: For the following tests:
    # Verify we intend to allow supplying a character-value query when the
    # species is known.  The code allows it (because it handles more than
    # one context) but it might not have been intended here.

    def test_get_with_char_param_returns_ok(self):
        response = self.client.get('/api/taxa/Fooium%20fooia/?c1=cv1_1')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_param_returns_not_found_if_no_species(self):
        response = self.client.get('/api/taxa/Not%20here/?c1=cv1_1')
        self.assertEqual(404, response.status_code)

    def test_get_with_char_param_returns_not_found_if_no_char(self):
        response = self.client.get('/api/taxa/Fooium%20fooia/?none=cv1_1')
        self.assertEqual(404, response.status_code)

    def test_get_with_char_param_returns_ok_if_bad_char_value(self):
        response = self.client.get('/api/taxa/Fooium%20fooia/?c1=badvalue')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_param_returns_no_item_if_bad_char_value(self):
        response = self.client.get('/api/taxa/Fooium%20fooia/?c1=badvalue')
        self.assertEqual(b'{}', response.content)

    def test_get_response_contains_habitat(self):
        response = self.client.get('/api/taxa/Fooium%20barula/')
        json_object = json.loads(response.content)
        self.assertTrue(json_object['habitat'])

    def test_get_response_habitat_has_multiple_values(self):
        response = self.client.get('/api/taxa/Fooium%20barula/')
        json_object = json.loads(response.content)
        self.assertEqual(2, len(json_object['habitat'])) # Expect 2 habitats.

    def test_get_response_most_characters_have_single_values(self):
        response = self.client.get('/api/taxa/Fooium%20barula/')
        json_object = json.loads(response.content)
        self.assertEqual('cv1_2', json_object['c1'])
        self.assertEqual('cv2', json_object['c2'])


class TaxaCountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_returns_ok(self):
        response = self.client.get('/api/taxa-count/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/taxa-count/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_with_character_value_param_returns_ok(self):
        response = self.client.get('/api/taxa-count/?c1=cv1_1')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_value_param_returns_not_found_if_no_char(self):
        response = self.client.get('/api/taxa-count/?none=cv1_1')
        self.assertEqual(404, response.status_code)


class TaxonImageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data(load_images=True)
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)
        _remove_content_images_dir()

    def test_get_returns_ok(self):
        response = self.client.get('/api/taxon-image/?species=Fooium%20barula')
        self.assertEqual(200, response.status_code)
        # TODO: test other params that can be passed; taxon id?

    def test_get_returns_json(self):
        response = self.client.get('/api/taxon-image/?species=Fooium%20barula')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_species(self):
        response = self.client.get('/api/taxon-image/?species=Not%20here')
        self.assertEqual(404, response.status_code)

    def test_get_returns_bad_request_when_no_params(self):
        response = self.client.get('/api/taxon-image/')
        self.assertEqual(400, response.status_code)

    def test_get_returns_data_when_images_exist(self):
        response = self.client.get('/api/taxon-image/?species=Fooium%20barula')
        json_object = json.loads(response.content)
        self.assertEqual(2, len(json_object))   # Expect 2 images.
        for image in json_object:
            self.assertEqual(str, type(image['url']))
            self.assertEqual(str, type(image['type']))
            self.assertEqual(int, type(image['rank']))
            self.assertEqual(str, type(image['title']))
            self.assertEqual(str, type(image['thumb_url']))
            self.assertEqual(str, type(image['large_thumb_url']))

    def test_get_returns_empty_list_when_images_do_not_exist(self):
        response = self.client.get('/api/taxon-image/?species=Fooium%20fooia')
        self.assertEqual(b'[]', response.content)


class PileGroupListTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/api/pilegroups/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/pilegroups/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])


class PileGroupTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_returns_ok(self):
        response = self.client.get('/api/pilegroups/pilegroup1/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/pilegroups/pilegroup1/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_pile_group(self):
        response = self.client.get('/api/pilegroups/nogroup/')
        self.assertEqual(404, response.status_code)


class PileListTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/api/piles/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/piles/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])


class PileTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_returns_ok(self):
        response = self.client.get('/api/piles/pile1/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/piles/pile1/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_pile(self):
        response = self.client.get('/api/piles/nopile/')
        self.assertEqual(404, response.status_code)


class CharacterListTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_returns_ok(self):
        response = self.client.get('/api/piles/pile1/characters/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/piles/pile1/characters/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_pile(self):
        response = self.client.get('/api/piles/nopile/characters/')
        self.assertEqual(404, response.status_code)

    def test_get_with_choose_best_param_returns_ok(self):
        response = self.client.get('/api/piles/pile1/characters/?choose_best=3')
        self.assertEqual(200, response.status_code)

    def test_get_with_exclude_chars_param_returns_ok(self):
        response = self.client.get(
            '/api/piles/pile1/characters/?exclude=c1')
        self.assertEqual(200, response.status_code)

    def test_get_with_character_groups_param_returns_ok(self):
        response = self.client.get(
            '/api/piles/pile1/characters/?character_groups=1')  # id of char group
        self.assertEqual(200, response.status_code)

    def test_get_with_nonexistent_char_group_returns_ok(self):
        response = self.client.get(
            '/api/piles/pile1/characters/?character_groups=0')  # id of char group
        self.assertEqual(200, response.status_code)

    def test_get_ignores_unknown_includes(self):
        response = self.client.get(
            '/api/piles/pile1/characters/?include=foo&include=c1&include=bar')
        self.assertEqual(200, response.status_code)


class CharacterValuesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_returns_ok(self):
        response = self.client.get('/api/piles/pile1/c1/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/piles/pile1/c1/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_character(self):
        response = self.client.get('/api/piles/pile1/nochar/')
        self.assertEqual(404, response.status_code)


class FamiliesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_lowercase_returns_ok(self):
        response = self.client.get('/api/families/fooaceae/')
        self.assertEqual(200, response.status_code)

    def test_get_titlecase_returns_ok(self):
        response = self.client.get('/api/families/Fooaceae/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/families/fooaceae/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_family(self):
        response = self.client.get('/api/families/no-family/')
        self.assertEqual(404, response.status_code)


class GeneraTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def setUp(self):
        _setLoggingLevelError(self)

    def tearDown(self):
        _restoreLoggingLevel(self)

    def test_get_lowercase_returns_ok(self):
        response = self.client.get('/api/genera/fooium/')
        self.assertEqual(200, response.status_code)

    def test_get_titlecase_returns_ok(self):
        response = self.client.get('/api/genera/Fooium/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_json(self):
        response = self.client.get('/api/genera/fooium/')
        self.assertEqual('application/json; charset=utf-8',
                         response['Content-Type'])

    def test_get_returns_not_found_when_nonexistent_genus(self):
        response = self.client.get('/api/genera/no-genus/')
        self.assertEqual(404, response.status_code)

import json
import os

from django.test import TestCase
from django.test.client import Client

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from django.core.files import File

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

    famfoo, c = models.Family.objects.get_or_create(name='Fooaceae')
    fambaz, c = models.Family.objects.get_or_create(name='Bazaceae')

    genfoo, c = models.Genus.objects.get_or_create(name='Fooium')
    genbaz, c = models.Genus.objects.get_or_create(name='Bazia')

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
            model='', app_label='core', defaults={'name': 'core'})
        # Create one image.
        im1 = models.ContentImage(alt='im1 alt', rank=1,
            creator='photographer A', image_type=image_type,
            description='im1 desc', content_type=content_type,
            object_id=bar.id)
        filename = 'huperzia-appressa-ha-dkausen-1.jpg'
        f = open('%s/%s' % (_testdata_dir(), filename), 'r')
        image_file = File(f)
        im1.image.save(filename, image_file)
        im1.save()
        f.close()
        # Create another image.
        im2 = models.ContentImage(alt='im2 alt', rank=2,
            creator='photographer B', image_type=image_type,
            description='im2 desc', content_type=content_type,
            object_id=bar.id)
        filename = 'huperzia-appressa-ha-dkausen-1.jpg'
        f = open('%s/%s' % (_testdata_dir(), filename), 'r')
        image_file = File(f)
        im2.image.save(filename, image_file)
        im2.save()
        f.close()
        # Add the images to the taxon.
        bar.images = [im1, im2]
        bar.save()

    pile1.species.add(foo)
    pile1.species.add(bar)
    pile1.species.add(abc)

    cg1 = models.CharacterGroup(name='cg1')
    cg1.save()

    c1 = models.Character(short_name='c1', character_group=cg1)
    c1.save()
    c2 = models.Character(short_name='c2', character_group=cg1)
    c2.save()
    c3 = models.Character(short_name='c3', character_group=cg1,
                          value_type='LENGTH')
    c3.save()

    cv1 = models.CharacterValue(value_str='cv1', character=c1)
    cv1.save()
    cv2 = models.CharacterValue(value_str='cv2', character=c1)
    cv2.save()
    cv3 = models.CharacterValue(value_min=5, value_max=11, character=c3)
    cv3.save()

    pile1.character_values.add(cv1)
    pile1.character_values.add(cv2)
    pile1.character_values.add(cv3)
    pile1.save()

    models.TaxonCharacterValue(taxon=foo, character_value=cv1).save()
    models.TaxonCharacterValue(taxon=bar, character_value=cv2).save()

    df1 = models.DefaultFilter(pile=pile1, character=c1, order=1,
                               key_characteristics='key characteristics 1',
                               notable_exceptions='notable exceptions 1')
    df1.save()

    df2 = models.DefaultFilter(pile=pile1, character=c2, order=2,
                               key_characteristics='key characteristics 2',
                               notable_exceptions='notable exceptions 2')
    df2.save()
    
    ppc1 = models.PlantPreviewCharacter(pile=pile1, character=c1, order=1)
    ppc1.save()
    
    ppc2 = models.PlantPreviewCharacter(pile=pile1, character=c2, order=2)
    ppc2.save()

    pile1.default_filters.members = [df1, df2]
    pile1.plant_preview_characters.members = [ppc1, ppc2]
    pile1.save()


# This is currently the "demo" page.  Its URL and view is actually specified
# in the core/ app.  TODO: consider moving the page elsewhere, and having a
# service "start" URI here.
class StartTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_html(self):
        response = self.client.get('/')
        self.assertEqual('text/html; charset=utf-8', response['Content-Type'])


class TaxonListTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/taxon/')
        self.assertEqual(200, response.status_code)

    # TODO: change URI from /taxon/ to /taxa/.

    # TODO: support non-trailing slash variant, using middleware redirect.
    
    def test_get_with_char_param_returns_ok(self):
        response = self.client.get('/taxon/?c1=cv1')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_param_returns_not_found_if_no_char(self):
        response = self.client.get('/taxon/?none=cv1')
        self.assertEqual(404, response.status_code)

    def test_get_with_char_param_returns_ok_if_bad_char_value(self):
        response = self.client.get('/taxon/?c1=badvalue')
        self.assertEqual(200, response.status_code)
        
    def test_get_with_char_param_returns_no_items_if_bad_char_value(self):
        response = self.client.get('/taxon/?c1=badvalue')
        expected = { 'items': [],
                     'identifier': 'scientific_name',
                     'label': 'scientific_name'}
        self.assertEqual(expected, json.loads(response.content))


class TaxonTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/taxon/Fooium%20barula/')
        self.assertEqual(200, response.status_code)

    # TODO: change URI from /taxon/ to /taxa/.

    # TODO: support non-trailing slash variant, using middleware redirect.
    
    def test_get_returns_not_found_when_nonexistent_species(self):
        response = self.client.get('/taxon/Not%20here/')
        self.assertEqual(404, response.status_code)

    # TODO: For the following tests:
    # Verify we intend to allow supplying a character-value query when the 
    # species is known.  The code allows it but it might not be needed.

    def test_get_with_char_param_returns_ok(self):
        response = self.client.get('/taxon/Fooium%20fooia/?c1=cv1')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_param_returns_not_found_if_no_species(self):
        response = self.client.get('/taxon/Not%20here/?c1=cv1')
        self.assertEqual(404, response.status_code)
        
    def test_get_with_char_param_returns_not_found_if_no_char(self):
        response = self.client.get('/taxon/Fooium%20fooia/?none=cv1')
        self.assertEqual(404, response.status_code)

    def test_get_with_char_param_returns_ok_if_bad_char_value(self):
        response = self.client.get('/taxon/Fooium%20fooia/?c1=badvalue')
        self.assertEqual(200, response.status_code)

    def test_get_with_char_param_returns_no_item_if_bad_char_value(self):
        response = self.client.get('/taxon/Fooium%20fooia/?c1=badvalue')
        self.assertEqual('{}', response.content)


class TaxonCountTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/taxon-count/')
        self.assertEqual(200, response.status_code)

    # TODO: change URI from /taxon-count/ to /taxa-count/.
    # (This is started in the code.)

    def test_get_with_character_value_param_returns_ok(self):
        response = self.client.get('/taxon-count/?c1=cv1')
        self.assertEqual(200, response.status_code)
        
    def test_get_with_char_value_param_returns_not_found_if_no_char(self):
        response = self.client.get('/taxon-count/?none=cv1')
        self.assertEqual(404, response.status_code)


class TaxonImageTestCase(TestCase):
    def setUp(self):
        _setup_sample_data(load_images=True)
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/taxon-image/?species=Fooium%20barula')
        self.assertEqual(200, response.status_code)
        # TODO: test other params that can be passed; taxon id?

    def test_get_returns_not_found_when_nonexistent_species(self):
        response = self.client.get('/taxon-image/?species=Not%20here')
        self.assertEqual(404, response.status_code)

    def test_get_returns_bad_request_when_no_params(self):
        response = self.client.get('/taxon-image/')
        self.assertEqual(400, response.status_code)

    def test_get_returns_data_when_images_exist(self):
        response = self.client.get('/taxon-image/?species=Fooium%20barula')
        json_object = json.loads(response.content)
        self.assertEqual(2, len(json_object))   # Expect 2 images.
        for image in json_object:
            self.assertEqual(int, type(image['thumb_height']))
            self.assertEqual(unicode, type(image['description']))
            self.assertEqual(int, type(image['thumb_width']))
            self.assertEqual(unicode, type(image['title']))
            self.assertEqual(unicode, type(image['url']))
            self.assertEqual(int, type(image['rank']))
            self.assertEqual(int, type(image['scaled_height']))
            self.assertEqual(unicode, type(image['url']))
            self.assertEqual(unicode, type(image['scaled_url']))
            self.assertEqual(unicode, type(image['thumb_url']))
            self.assertEqual(unicode, type(image['type']))
            self.assertEqual(int, type(image['scaled_width']))

    def test_get_returns_empty_list_when_images_do_not_exist(self):
        response = self.client.get('/taxon-image/?species=Fooium%20fooia')
        self.assertEqual('[]', response.content)


class PileGroupListTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()
        
    def test_get_returns_ok(self):
        response = self.client.get('/pilegroups/')
        self.assertEqual(200, response.status_code)


class PileGroupTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()
        
    def test_get_returns_ok(self):
        # TODO: add trailing slash to canonical URL and support omitting the
        # trailing slash via middleware redirect.
        response = self.client.get('/pilegroups/pilegroup1')
        self.assertEqual(200, response.status_code)

    def test_get_returns_not_found_when_nonexistent_pile_group(self):
        response = self.client.get('/pilegroups/nogroup')
        self.assertEqual(404, response.status_code)

    def test_delete_returns_no_content(self):
        response = self.client.delete('/pilegroups/pilegroup1')
        self.assertEqual(204, response.status_code)

    def test_put_returns_ok(self):
        response = self.client.put('/pilegroups/pilegroup1',
                                   data={'friendly_name': 'Pile Group 1'})
        self.assertEqual(200, response.status_code)


class PileListTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/piles/')
        self.assertEqual(200, response.status_code)


class PileTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/piles/pile1/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_not_found_when_nonexistent_pile(self):
        response = self.client.get('/piles/nopile/')
        self.assertEqual(404, response.status_code)

    def test_delete_returns_no_content(self):
        response = self.client.delete('/piles/pile1/')
        self.assertEqual(204, response.status_code)

    def test_put_returns_ok(self):
        response = self.client.put('/piles/pile1/',
                                   data={'friendly_name': 'Pile 1'})
        self.assertEqual(200, response.status_code)


class CharacterListTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/piles/pile1/characters/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_not_found_when_nonexistent_pile(self):
        response = self.client.get('/piles/nopile/characters/')
        self.assertEqual(404, response.status_code)

    def test_get_with_choose_best_param_returns_ok(self):
        response = self.client.get('/piles/pile1/characters/?choose_best=3')
        self.assertEqual(200, response.status_code)

    def test_get_with_include_filter_param_returns_ok(self):
        response = self.client.get(
            '/piles/pile1/characters/?include_filter=1')
        self.assertEqual(200, response.status_code)


class CharacterValuesTestCase(TestCase):
    def setUp(self):
        _setup_sample_data()
        self.client = Client()

    def test_get_returns_ok(self):
        response = self.client.get('/piles/pile1/c1/')
        self.assertEqual(200, response.status_code)

    def test_get_returns_not_found_when_nonexistent_pile(self):
        response = self.client.get('/piles/nopile/c1/')
        self.assertEqual(404, response.status_code)

    def test_get_returns_not_found_when_nonexistent_character(self):
        response = self.client.get('/piles/pile1/nochar/')
        self.assertEqual(404, response.status_code)


    # Beginning (baseline) code coverage:
    #
    # handlers.py: 39% (everything else is 100%)
    #
    # After adding tests so far, coverage for handlers.py is 98%.
    
    # Organization/approach:
    #
    # Separate TestCase for each URI.
    #
    # For each URI, what to test?
    #
    # - Normal and non-normal status code(s) for each of the supported HTTP 
    #   methods.
    # - Supported/unsupported HTTP methods.
    # - Representations accepted from the client for each of the supported
    #   methods.
    # - Representations served to the client for each of the supported
    #   methods.
    # - Content type (MIME type) of the response(s) for each of the supported
    #   methods.
    # - Error conditions ("what might go wrong?").
    # - Header values accepted from the client for each of the supported
    #   methods.
    # - Header values served to the client for each of the supported methods.
    # - Canonical URIs vs. representation-specific URIs (and Content-Location
    #   header), if applicable.
    #
    # - Trailing-slash (or not, or both) - if applicable.
    # TODO: activate middleware for redirecting on missing trailing slashes:
    # django.middleware.common.CommonMiddleware
    #
    # Also TODO: name all URLs in urls.py, relating the URL name and TestCase
    # name, in order to make these names help the reader find and relate
    # things more easily.


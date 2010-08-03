from django.test import TestCase
from django.test.client import Client

from gobotany.simplekey.models import Collection

class SimpleTests(TestCase):

    def test_collection_start_page(self):
        c = Client()
        r = c.get('/simple/collections/start/')

        assert 'Ferns' in r.content
        assert 'Woody plants' in r.content
        assert 'Give me more choices' in r.content

        assert '/simple/collections/aquatics/' in r.content
        assert '/simple/collections/continue1/' in r.content

    def test_subway_map(self):
        c = Client()
        r = c.get('/simple/collections/start/')
        # put complicated test here

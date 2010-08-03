from django.test import TestCase
from django.test.client import Client

from gobotany.simplekey.models import Collection

class SimpleTests(TestCase):

    def test_collection_start_page(self):
        c = Client()
        c.get('/simple/collections/start/')

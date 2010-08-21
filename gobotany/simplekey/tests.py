from django.test import TestCase
from django.test.client import Client

class SimpleTests(TestCase):
    fixtures = ['page_data']

    def test_start_page(self):
        c = Client()
        r = c.get('/simple/1/')

        assert 'Give me more choices' in r.content

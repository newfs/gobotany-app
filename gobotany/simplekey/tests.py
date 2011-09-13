from django.test import TestCase
from django.test.client import Client

class SimpleTests(TestCase):
    fixtures = ['page_data']

    def test_start_page(self):
        c = Client()
        r = c.get('/1/')
        assert 'Which group best describes your plant?' in r.content

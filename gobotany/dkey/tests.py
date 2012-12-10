"""Tests of whether our basic site layout is present."""

from django.test.client import Client

from gobotany.libtest import FunctionalCase

class HomeTests(FunctionalCase):

    def test_home_page(self):
        self.get('/dkey/')

    def test_group_1(self):
        self.get('/dkey/group-1/')

    def test_family(self):
        self.get('/dkey/equisetaceae/')

    def test_genus(self):
        self.get('/dkey/equisetum/')

    def test_species(self):
        # No species-level pages in the D. Key itself. Links to site-wide
        # species pages.
        client = Client()
        response = client.get('/dkey/equisetum-hyemale/')
        self.assertEqual(response.status_code, 404)

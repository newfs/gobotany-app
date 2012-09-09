"""Tests of whether our basic site layout is present."""

from gobotany.libtest import FunctionalCase, Client

class FunctionalTests(FunctionalCase):

    def test_front_page(self):
        c = Client()
        response = c.get('/')

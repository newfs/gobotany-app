from django.test import TestCase
from gobotany import botany


class SimpleTests(TestCase):

    def test_environment(self):
        self.assert_(True)


class APITests(TestCase):

    def test_query_species(self):
        self.assert_(len(botany.query_species(scientific_name='foo')) == 0)

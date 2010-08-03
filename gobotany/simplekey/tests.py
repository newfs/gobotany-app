from django.test import TestCase
from django.test.client import Client

class SimpleTests(TestCase):

    def test_environment(self):
        self.assert_(True)

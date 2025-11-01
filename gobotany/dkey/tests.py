"""Tests of whether our basic site layout is present."""

import unittest

from django.test import TestCase
from django.test.client import Client

from gobotany.dkey import models

class HomeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        top_page = models.Page(chapter='', title='Key to the Families',
            rank='top')
        top_page.save()
        group1 = models.Page(chapter='Key to the Families', title='Group 1',
            rank='group')
        group1.save()
        family = models.Page(chapter='Monilophytes', title='Equisetaceae',
            rank='family')
        family.save()
        genus = models.Page(chapter='Monilophytes', title='Equisetum',
            rank='genus')
        genus.save()
        cls.client = Client()

    def test_home_page(self):
        response = self.client.get('/dkey/')
        self.assertEqual(response.status_code, 200)

    def test_group_1(self):
        response = self.client.get('/dkey/group-1/')
        self.assertEqual(response.status_code, 200)

    def test_family(self):
        response = self.client.get('/dkey/equisetaceae/')
        self.assertEqual(response.status_code, 200)

    def test_genus(self):
        response = self.client.get('/dkey/equisetum/')
        self.assertEqual(response.status_code, 200)

    def test_species(self):
        # No species-level pages in the D. Key itself. Links to site-wide
        # species pages.
        response = self.client.get('/dkey/equisetum-hyemale/')
        self.assertEqual(response.status_code, 404)

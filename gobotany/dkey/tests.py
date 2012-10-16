"""Tests of whether our basic site layout is present."""

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
        self.get('/dkey/equisetum-hyemale/')

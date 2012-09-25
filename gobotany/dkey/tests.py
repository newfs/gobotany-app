"""Tests of whether our basic site layout is present."""

from gobotany.libtest import FunctionalCase

class HomeTests(FunctionalCase):

    def test_home_page(self):
        self.get('/dkey/')

    def test_family_groups(self):
        self.get('/dkey/Family-Groups/')

    def test_group_1(self):
        self.get('/dkey/Group-1/')

    def test_family(self):
        self.get('/dkey/Equisetaceae/')

    def test_genus(self):
        self.get('/dkey/Equisetum/')

    def test_species(self):
        self.get('/dkey/Equisetum-hyemale/')

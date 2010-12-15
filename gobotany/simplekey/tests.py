from django.test import TestCase
from django.test.client import Client

from gobotany.simplekey import views

class SimpleTests(TestCase):
    fixtures = ['page_data']

    def test_start_page(self):
        c = Client()
        r = c.get('/simple/1/')
        assert 'More choices' in r.content


class SpeciesDistributionAndConservationStatusTests(TestCase):

    DISTRIBUTION = ['MA', 'VT']

    def test_get_state_status_is_present(self):
        status = views._get_state_status('MA', self.DISTRIBUTION)
        self.assertEqual('present', status)

    def test_get_state_status_is_absent(self):
        status = views._get_state_status('CT', self.DISTRIBUTION)
        self.assertEqual('absent', status)

    def test_get_state_status_is_absent_and_has_conservation_status(self):
        # Exclude extinct status ('X') from this list; it is an exception
        # and has its own test.
        status_codes = ['E', 'T', 'SC', 'SC*', 'H', 'C']
        for status_code in status_codes:
            status = views._get_state_status('CT', self.DISTRIBUTION,
                conservation_status_code=status_code)
            self.assertEqual('absent', status)

    def test_get_state_status_is_endangered(self):
        status = views._get_state_status('MA', self.DISTRIBUTION,
                                         conservation_status_code='E')
        self.assertEqual('present, endangered', status)

    def test_get_state_status_is_threatened(self):
        status = views._get_state_status('MA', self.DISTRIBUTION,
                                         conservation_status_code='T')
        self.assertEqual('present, threatened', status)

    def test_get_state_status_has_special_concern(self):
        status_codes = ['SC', 'SC*']
        for status_code in status_codes:
            status = views._get_state_status('MA', self.DISTRIBUTION,
                conservation_status_code=status_code)
            self.assertEqual('present, special concern', status)

    def test_get_state_status_is_historic(self):
        status = views._get_state_status('MA', self.DISTRIBUTION,
                                         conservation_status_code='H')
        self.assertEqual('present, historic', status)

    def test_get_state_status_is_extinct(self):
        status = views._get_state_status('ME', self.DISTRIBUTION,
                                         conservation_status_code='X')
        self.assertEqual('absent, extinct', status)

    def test_get_state_status_is_rare(self):
        status = views._get_state_status('MA', self.DISTRIBUTION,
                                         conservation_status_code='C')
        self.assertEqual('present, rare', status)

    def test_get_state_status_is_invasive(self):
        status = views._get_state_status('MA', self.DISTRIBUTION,
                                         is_invasive=True)
        self.assertEqual('present, invasive', status)

    def test_get_state_status_is_invasive_and_prohibited(self):
        status = views._get_state_status('MA', self.DISTRIBUTION,
                                         is_invasive=True,
                                         is_prohibited=True)
        self.assertEqual('present, invasive, prohibited', status)

    def test_get_state_status_is_absent_and_prohibited(self):
        status = views._get_state_status('ME', self.DISTRIBUTION,
                                         is_prohibited=True)
        self.assertEqual('absent, prohibited', status)

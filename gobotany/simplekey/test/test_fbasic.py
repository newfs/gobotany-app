"""Selenium-driven basic functional tests of Go Botany."""

import unittest2
from contextlib import contextmanager
from selenium import webdriver

host = 'http://localhost:8000'
base = '/simple'

class FunctionalTestCase(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Chrome()
        #cls.driver = webdriver.Firefox()

    def setUp(self):
        self.driver.implicitly_wait(0)  # reset to zero wait time
        self.css = self.driver.find_elements_by_css_selector
        self.css1 = self.driver.find_element_by_css_selector

    # Helpers

    def get(self, path):
        """Retrieve a URL, and return the driver object."""
        self.driver.get(host + base + path)
        return self.driver

    def find(self, css):
        return self.driver.find_elements_by_css_selector(css)

    @contextmanager
    def wait(self, seconds):
        self.driver.implicitly_wait(seconds)
        try:
            yield
        finally:
            self.driver.implicitly_wait(0)


class BasicFunctionalTests(FunctionalTestCase):

    # Tests

    def test_front_page(self):
        d = self.get('/')
        self.assertEqual(
            d.title, u'Go Botany: New England Wild Flower Society')
        e = d.find_element_by_link_text('Get Started')
        self.assertEqual(e.get_attribute('href'), '1/')

    def test_ubergroup_pages(self):
        d = self.get('/1/')
        h3 = self.find('h3')
        self.assertEqual(len(h3), 3)
        assert h3[0].text.startswith('Ferns')
        assert h3[1].text.startswith('Woody Plants')
        assert h3[2].text.startswith('Aquatic Plants')
        d.find_element_by_link_text('Show me other groups').click()
        h3 = self.find('h3')
        self.assertEqual(len(h3), 1)
        assert h3[0].text.startswith('Graminoids')
        d.find_element_by_link_text('Show me other groups').click()
        h3 = self.find('h3')
        self.assertEqual(len(h3), 1)
        assert h3[0].text.startswith('Monocots')
        d.find_element_by_link_text('Show me other groups').click()
        h3 = self.find('h3')
        self.assertEqual(len(h3), 1)
        assert h3[0].text.startswith('Non-Monocots')
        e = d.find_elements_by_link_text('Show me other groups')
        self.assertEqual(e, [])

        # Do group links get constructed correctly?
        e = d.find_element_by_link_text('My plant is in this group.')
        self.assertEqual(e.get_attribute('href'), base + '/non-monocots/')

    def test_group_page(self):
        d = self.get('/ferns/')
        q = self.find('h3')
        self.assertEqual(len(q), 3)
        assert q[0].text.startswith('Equisetaceae')
        assert q[1].text.startswith('Lycophytes')
        assert q[2].text.startswith('Monilophytes')
        q = d.find_elements_by_link_text('My plant is in this group.')
        b = base + '/ferns'
        self.assertEqual(q[0].get_attribute('href'), b + '/equisetaceae/')
        self.assertEqual(q[1].get_attribute('href'), b + '/lycophytes/')
        self.assertEqual(q[2].get_attribute('href'), b + '/monilophytes/')


class FilterFunctionalTests(FunctionalTestCase):

    def wait_on_species(self, expected_count):
        """Wait for a new batch of species to be displayed."""
        with self.wait(12):
            self.css1('#plant-listing li li')
        q = self.css('#plant-listing li li')
        self.assertEqual(len(q), expected_count)
        count_words = self.css1('.count').text.split()  # "9 species matched"
        count = int(count_words[0])
        self.assertEqual(count, expected_count)
        return q

    def test_filter_page_narrows(self):

        # Does the page load and show 18 species?

        d = self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        d.find_element_by_link_text('New England state').click()
        d.find_element_by_css_selector('[value="Rhode Island"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(13)

        # filter on bogs

        d.find_element_by_link_text('Habitat').click()
        d.find_element_by_css_selector('[value="bogs"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(1)

        # switch from bogs to forest

        d.find_element_by_css_selector('[value="forest"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(6)

        # clear the New England state

        d.find_element_by_css_selector('#state_distribution .clear').click()
        self.wait_on_species(9)

    def test_quickly_press_apply_and_clear(self):

        # Does pressing the "apply" button and a "clear" link
        # simultaneously result in the result being updated twice?

        d = self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        d.find_element_by_link_text('New England state').click()
        d.find_element_by_css_selector('[value="Rhode Island"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(13)

        # filter on bogs

        d.find_element_by_link_text('Habitat').click()
        d.find_element_by_css_selector('[value="bogs"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(1)

        # clear the New England state AND press "apply" again

        d.find_element_by_css_selector('#state_distribution .clear').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(1)

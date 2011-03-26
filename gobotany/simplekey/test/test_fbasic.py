"""Selenium-driven basic functional tests of Go Botany."""

import unittest2
from selenium import webdriver

host = 'http://localhost:8000'
base = '/simple'

class BasicFunctionalTests(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        #self.driver = webdriver.Chrome()
        cls.driver = webdriver.Firefox()

    # Helpers

    def get(self, path):
        """Retrieve a URL, and return the driver object."""
        self.driver.get(host + base + path)
        return self.driver

    def find(self, css):
        return self.driver.find_elements_by_css_selector(css)

    # Tests

    def test_front_page(self):
        d = self.get('/')
        self.assertEqual(
            d.title, u'Go Botany: New England Wild Flower Society')
        e = d.find_element_by_link_text('Get Started')
        self.assertEqual(e.get_attribute('href'), '1/')

    def test_group_pages(self):
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

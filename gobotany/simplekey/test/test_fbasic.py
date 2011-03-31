"""Selenium-driven basic functional tests of Go Botany.

Two environmental variables control the behavior of these tests.

* SELENIUM - If this variable is not provided, then Selenium simply
  starts up a local browser.  But if it is provided, then it should be
  the URL of a selenium remote server - either one you have set up on
  one of your own machines by running the "standalone" server you can
  download from their web site, or one run by Sauce Labs, who will
  provide the URL for you on their web site.

* SIMPLEHOST - The hostname on which you have the Simple Key running.
  Defaults to `localhost` if not set.

"""
import os
import unittest2
from contextlib import contextmanager
from selenium import webdriver

class FunctionalTestCase(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        if 'SELENIUM' in os.environ:
            cls.driver = webdriver.Remote(os.environ['SELENIUM'], {
                    "browserName": "internet explorer",
                    #"version": "9",
                    "platform": "WINDOWS",
                    "javascriptEnabled": True,
                    "max-duration": 300,
                    })
        if 'SIMPLEHOST' in os.environ:
            cls.host = 'http://' + os.environ['SIMPLEHOST']
            cls.base = '/simple'
        else:
            cls.driver = webdriver.Chrome()
            cls.host = 'http://localhost:8000'
            cls.base = '/simple'

    @classmethod
    def tearDownClass(cls):
        cls.driver.stop_client()
        del cls.driver

    def setUp(self):
        self.driver.implicitly_wait(0)  # reset to zero wait time
        self.css = self.driver.find_elements_by_css_selector
        self.css1 = self.driver.find_element_by_css_selector

    # Helpers

    def url(self, path):
        """Compute and return a site URL."""
        return self.base + path

    def get(self, path):
        """Retrieve a URL, and return the driver object."""
        self.driver.get(self.host + self.url(path))
        return self.driver

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
        h3 = self.css('h3')
        self.assertEqual(len(h3), 3)
        assert h3[0].text.startswith('Ferns')
        assert h3[1].text.startswith('Woody Plants')
        assert h3[2].text.startswith('Aquatic Plants')
        d.find_element_by_link_text('Show me other groups').click()
        h3 = self.css('h3')
        self.assertEqual(len(h3), 1)
        assert h3[0].text.startswith('Graminoids')
        d.find_element_by_link_text('Show me other groups').click()
        h3 = self.css('h3')
        self.assertEqual(len(h3), 1)
        assert h3[0].text.startswith('Monocots')
        d.find_element_by_link_text('Show me other groups').click()
        h3 = self.css('h3')
        self.assertEqual(len(h3), 1)
        assert h3[0].text.startswith('Non-Monocots')
        e = d.find_elements_by_link_text('Show me other groups')
        self.assertEqual(e, [])

        # Do group links get constructed correctly?
        e = d.find_element_by_link_text('My plant is in this group.')
        self.assertEqual(e.get_attribute('href'),
                         self.base + '/non-monocots/')

    def test_group_page(self):
        d = self.get('/ferns/')
        q = self.css('h3')
        self.assertEqual(len(q), 3)
        assert q[0].text.startswith('Equisetaceae')
        assert q[1].text.startswith('Lycophytes')
        assert q[2].text.startswith('Monilophytes')
        q = d.find_elements_by_link_text('My plant is in this group.')
        b = self.base + '/ferns'
        self.assertEqual(q[0].get_attribute('href'), b + '/equisetaceae/')
        self.assertEqual(q[1].get_attribute('href'), b + '/lycophytes/')
        self.assertEqual(q[2].get_attribute('href'), b + '/monilophytes/')


class FilterFunctionalTests(FunctionalTestCase):

    def wait_on_species(self, expected_count):
        """Wait for a new batch of species to be displayed."""
        with self.wait(12):
            self.css1('div.plant-list div.plant')
        q = self.css('div.plant-list div.plant')
        self.assertEqual(len(q), expected_count)
        count_words = self.css1('h3 .species-count').text.split()  # "9 species matched"
        count = int(count_words[0])
        self.assertEqual(count, expected_count)
        return q

    def test_filter_page_narrows(self):

        # Does the page load and show 18 species?

        d = self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        self.css1('#state_distribution a.option').click()
        self.css1('[value="Rhode Island"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(13)

        # filter on bogs

        self.css1('#habitat a.option').click()
        self.css1('[value="bogs"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(1)

        # switch from bogs to forest

        self.css1('[value="forest"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(6)

        # clear the New England state

        self.css1('#state_distribution .clear').click()
        self.wait_on_species(9)

    def test_quickly_press_apply_twice(self):

        # Does a double tap of "apply" load species twice?

        d = self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        #d.find_element_by_link_text('New England state').click()
        self.css1('#state_distribution a.option').click()
        self.css1('[value="Rhode Island"]').click()
        d.find_element_by_name('apply').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(13)

    def test_quickly_press_apply_and_clear(self):

        # Does pressing the "apply" button and a "clear" link
        # simultaneously result in the result being updated twice?

        d = self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        self.css1('#state_distribution a.option').click()
        self.css1('[value="Rhode Island"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(13)

        # filter on bogs

        self.css1('#habitat a.option').click()
        self.css1('[value="bogs"]').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(1)

        # clear the New England state AND press "apply" again

        self.css1('#state_distribution .clear').click()
        d.find_element_by_name('apply').click()
        self.wait_on_species(1)

    def test_thumbnail_presentation(self):

        # Are different images displayed when you select "Show:" choices?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        e = self.css1('#plant-dendrolycopodium-dendroideum img')
        assert '-ha-' in e.get_attribute('src')
        self.css1('#results-display .dijitSelectLabel').click()
        self.css1('#dijit_MenuItem_2_text').click()  # 'shoots'
        assert '-sh-' in e.get_attribute('src')

    def test_get_more_filters(self):
        FILTERS_CSS = 'ul.option-list li'
        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        filters = self.css(FILTERS_CSS)
        n = len(filters)
        self.css1('#sidebar a.get-choices').click()
        filters = self.css(FILTERS_CSS)
        self.assertEqual(len(filters), n + 3)


class GlossaryFunctionalTests(FunctionalTestCase):

    def test_help_start_links_to_glossary(self): 
        d = self.get('/help/start/')
        e = d.find_element_by_link_text('Glossary')
        self.assertEqual(e.get_attribute('href'),
                         self.url('/help/glossary/a/'))

    def test_glossary_a_page_contains_a_terms(self):
        d = self.get('/help/glossary/a/')
        xterms = self.css('h2')
        self.assertEqual(xterms[0].text[0], 'a')
        self.assertEqual(xterms[-1].text[0], 'a')

    def test_glossary_g_page_contains_g_terms(self):
        d = self.get('/help/glossary/g/')
        xterms = self.css('h2')
        self.assertEqual(xterms[0].text[0], 'g')
        self.assertEqual(xterms[-1].text[0], 'g')

    def test_glossary_z_page_contains_z_terms(self):
        d = self.get('/help/glossary/z/')
        xterms = self.css('h2')
        self.assertEqual(xterms[0].text[0], 'z')
        self.assertEqual(xterms[-1].text[0], 'z')

    def test_glossary_g_page_does_not_link_to_itself(self):
        d = self.get('/help/glossary/g/')
        e = d.find_elements_by_link_text('G')
        self.assertEqual(len(e), 0)

    def test_glossary_g_page_link_to_other_letters(self):
        d = self.get('/help/glossary/g/')
        for letter in 'ABCWYZ':  # 'X' currently has no terms
            e = d.find_elements_by_link_text(letter)
            self.assertTrue(len(e))

    def test_glossary_g_page_link_is_correct(self):
        d = self.get('/help/glossary/a/')
        e = d.find_element_by_link_text('G')
        self.assertEqual(e.get_attribute('href'),
                         self.url('/help/glossary/g/'))

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
import time
import unittest2
from contextlib import contextmanager
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException
    )
from selenium.webdriver.common.keys import Keys

def is_displayed(element):
    """Return whether an element is visible on the page."""
    try:
        return element.is_displayed()
    except StaleElementReferenceException:
        return False

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
        else:
            #cls.driver = webdriver.Firefox()
            cls.driver = webdriver.Chrome()

        if 'SIMPLEHOST' in os.environ:
            cls.host = 'http://' + os.environ['SIMPLEHOST']
            cls.base = ''
        else:
            cls.host = 'http://localhost:8000'
            cls.base = ''

    @classmethod
    def tearDownClass(cls):
        cls.driver.stop_client()
        del cls.driver

    def setUp(self):
        self.driver.implicitly_wait(0)  # reset to zero wait time
        self.css1 = self.driver.find_element_by_css_selector

    # Helpers

    def css(self, *args, **kw):
        elements = self.driver.find_elements_by_css_selector(*args, **kw)
        return [ e for e in elements if is_displayed(e) ]

    def url(self, path):
        """Compute and return a site URL."""
        return self.base + path

    def aurl(self, path):
        """Compute and return a full URL that includes the hostname."""
        return self.host + self.url(path)

    def get(self, path):
        """Retrieve a URL, and return the driver object."""
        self.driver.get(self.aurl(path))
        return self.driver

    @contextmanager
    def wait(self, seconds):
        self.driver.implicitly_wait(seconds)
        try:
            yield
        finally:
            self.driver.implicitly_wait(0)

    def wait_on(self, timeout, function, *args, **kw):
        t0 = t1 = time.time()
        while t1 - t0 < timeout:
            try:
                v = function(*args, **kw)
                if v:
                    return v
            except NoSuchElementException:
                pass
            time.sleep(0.1)
            t1 = time.time()
        return function(*args, **kw)  # one last try to really raise exception

    def wait_until_disappear(self, timeout, selector):
        t0 = t1 = time.time()
        while t1 - t0 < timeout:
            elements = self.css(selector)
            if len(elements) == 0:
                return
            time.sleep(0.1)
            t1 = time.time()
        raise RuntimeError(
            'after %s seconds there are still %s elements that match %r'
            % (timeout, len(elements), selector))

class BasicFunctionalTests(FunctionalTestCase):

    # Tests

    def test_front_page(self):
        d = self.get('/')
        self.assertEqual(
            d.title, u'Go Botany: New England Wild Flower Society')
        e = d.find_element_by_link_text('Get Started')
        self.assertEqual(e.get_attribute('href'), '/help/start/')
        # Once you have selected "don't show me this", should change to:
        # self.assertEqual(e.get_attribute('href'), '/1/')

    def test_ubergroup_pages(self):
        d = self.get('/1/')
        h3 = self.css('h3')
        self.assertEqual(len(h3), 3)
        assert h3[0].text.startswith('Ferns')
        assert h3[1].text.startswith('Woody Plants')
        assert h3[2].text.startswith('Aquatic Plants')
        d.find_element_by_link_text('Show me other groups').click()
        h3 = self.css('h3')
        self.assertEqual(len(h3), 3)
        assert h3[0].text.startswith('Graminoids')
        assert h3[1].text.startswith('Monocots')
        assert h3[2].text.startswith('Non-Monocots')
        e = d.find_elements_by_link_text('Show me other groups')
        self.assertEqual(e, [])

        # Do group links get constructed correctly?
        e = d.find_element_by_link_text('My plant is in this group.')
        self.assertEqual(e.get_attribute('href'), '/graminoids/')

    def test_group_page(self):
        d = self.get('/ferns/')
        q = self.css('h3')
        self.assertEqual(len(q), 3)
        assert q[0].text.startswith('Equisetaceae')
        assert q[1].text.startswith('Lycophytes')
        assert q[2].text.startswith('Monilophytes')
        q = d.find_elements_by_link_text('My plant is in this subgroup.')
        self.assertEqual(q[0].get_attribute('href'), '/ferns/equisetaceae/')
        self.assertEqual(q[1].get_attribute('href'), '/ferns/lycophytes/')
        self.assertEqual(q[2].get_attribute('href'), '/ferns/monilophytes/')


class FilterFunctionalTests(FunctionalTestCase):

    def wait_on_species(self, expected_count):
        """Wait for a new batch of species to be displayed."""
        self.wait_on(5, self.css1, 'div.plant-list div.plant')

        # Returning several hundred divs takes ~10 seconds, so we have
        # jQuery count the divs for us and just return the count.

        plant_div_count = self.driver.execute_script(
            "return $('div.plant-list div.plant').length;")
        self.assertEqual(plant_div_count, expected_count)

        # Split "9 species matched" into ["9", "species", "matched"].

        count_words = self.css1('h3 .species-count').text.split()
        count = int(count_words[0])
        self.assertEqual(count, expected_count)

    def test_multiple_choice_filters(self):

        # Does the page load and show 18 species?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        self.css1('#state_distribution a.option').click()
        count = self.css1('[value="Rhode Island"] + .label + .count').text
        self.assertEqual(count, '(13)')
        self.css1('[value="Rhode Island"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(13)

        # filter on bogs

        self.css1('#habitat a.option').click()
        count = self.css1('[value="bogs"] + .label + .count').text
        self.assertEqual(count, '(1)')
        self.css1('[value="bogs"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(1)

        # switch from bogs to forest

        self.css1('[value="forest"]').click()
        count = self.css1('[value="forest"] + .label + .count').text
        self.assertEqual(count, '(6)')
        self.css1('.apply-btn').click()
        self.wait_on_species(6)

        # clear the New England state

        self.css1('#state_distribution .clear-filter').click()
        self.wait_on_species(9)

    def list_family_choices(self):
        b = self.css1('[widgetid="family_select"] .dijitArrowButtonInner')
        b.click()
        items = self.wait_on(4, self.css, '#family_select_popup li')
        texts = [ item.text for item in items ]
        b.click()
        return texts

    def list_genus_choices(self):
        b = self.css1('[widgetid="genus_select"] .dijitArrowButtonInner')
        b.click()
        items = self.wait_on(4, self.css, '#genus_select_popup li')
        texts = [ item.text for item in items ]
        b.click()
        return texts

    def test_family_genus_filters(self):

        all_families = [
            u'Huperziaceae', u'Isoetaceae', u'Lycopodiaceae',
            u'Selaginellaceae',
            ]
        all_genera = [
            u'Dendrolycopodium', u'Diphasiastrum', u'Huperzia',
            u'Isoetes', u'Lycopodiella', u'Lycopodium', u'Selaginella',
            u'Spinulum',
            ]

        # Does the page load and show 18 species?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # Do the family and genus dropdowns start by displaying all options?

        self.assertEqual(self.list_genus_choices(), all_genera)
        self.assertEqual(self.list_family_choices(), all_families)

        # Try selecting a family.

        self.css1('#family_select').send_keys(u'Lycopodiaceae', Keys.RETURN)
        self.wait_on_species(11)
        self.assertEqual(self.list_family_choices(), all_families)
        self.assertEqual(self.list_genus_choices(), [
                u'Dendrolycopodium', u'Diphasiastrum',
                u'Lycopodiella', u'Lycopodium', u'Spinulum',
                ])

        # Clear the family.

        self.css1('#clear_family').click()
        self.assertEqual(self.list_family_choices(), all_families)
        self.assertEqual(self.list_genus_choices(), all_genera)

        # Try selecting a genus first.

        self.css1('#genus_select').send_keys(u'Lycopodium', Keys.RETURN)
        self.wait_on_species(2)
        self.assertEqual(self.list_family_choices(), [u'Lycopodiaceae'])
        self.assertEqual(self.list_genus_choices(), all_genera)

        # Select the one family that is now possible.

        self.css1('#family_select').send_keys(u'Lycopodiaceae', Keys.RETURN)
        self.wait_on_species(2)
        self.assertEqual(self.list_family_choices(), [u'Lycopodiaceae'])
        self.assertEqual(self.list_genus_choices(), [
                u'Dendrolycopodium', u'Diphasiastrum',
                u'Lycopodiella', u'Lycopodium', u'Spinulum',
                ])

        # Clear the genus, leaving the family in place.

        self.css1('#clear_genus').click()
        self.wait_on_species(11)
        self.assertEqual(self.list_family_choices(), all_families)
        self.assertEqual(self.list_genus_choices(), [
                u'Dendrolycopodium', u'Diphasiastrum',
                u'Lycopodiella', u'Lycopodium', u'Spinulum',
                ])

    def test_quickly_press_apply_twice(self):

        # Does a double tap of "apply" load species twice?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        #d.find_element_by_link_text('New England state').click()
        self.css1('#state_distribution a.option').click()
        self.css1('[value="Rhode Island"]').click()
        self.css1('.apply-btn').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(13)

    def test_quickly_press_apply_and_clear(self):

        # Does pressing the "apply" button and a "clear" link
        # simultaneously result in the result being updated twice?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        self.css1('#state_distribution a.option').click()
        self.css1('[value="Rhode Island"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(13)

        # filter on bogs

        self.css1('#habitat a.option').click()
        self.css1('[value="bogs"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(1)

        # clear the New England state AND press "apply" again

        self.css1('#state_distribution .clear-filter').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(1)

    def OFF_test_thumbnail_presentation(self):

        # Currently turned OFF because thumbnail images are no longer
        # loading on Brandon's dev machine when he runs an import - is
        # this because he's running the wrong data import ("import-data"
        # vs "import-sample"), and only one of them loads images without
        # having the huge image database?

        # Are different images displayed when you select "Show:" choices?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        e = self.css1('.plant-list img')
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

        # Hacky, pile-specific way to wait on the choices to appear:
        self.wait_on(1, self.css, '#spore_surface')
        filters = self.css(FILTERS_CSS)
        self.assertEqual(len(filters), n + 3)

    def test_length_filter(self):
        self.get('/non-monocots/remaining-non-monocots/'
                 '#_filters=family,genus,plant_height_rn'
                 '&_visible=plant_height_rn')
        self.wait_on_species(499)
        sidebar_value_span = self.css1('#plant_height_rn .value')
        range_div = self.css1('.permitted_ranges')
        measure_input = self.css1('input[name="measure"]')
        instructions = self.css1('.instructions')
        apply_button = self.css1('.apply-btn')

        self.assertIn(' 10 mm', range_div.text)
        self.assertIn(' 15000 mm', range_div.text)
        self.assertIn('enter a valid', instructions.text)

        # Type in a big number and watch the number of advertised
        # matching species change with each digit.

        measure_input.send_keys('1')
        self.assertIn('enter a valid', instructions.text)

        measure_input.send_keys('0')  # '10'
        self.assertIn('to the 3 matching species', instructions.text)

        measure_input.send_keys('0')  # '100'
        self.assertIn('to the 175 matching species', instructions.text)

        measure_input.send_keys('0')  # '1000'
        self.assertIn('to the 157 matching species', instructions.text)

        measure_input.send_keys('0')  # '10000'
        self.assertIn('to the 1 matching species', instructions.text)

        measure_input.send_keys('0')  # '100000'
        self.assertIn('enter a valid', instructions.text)

        # Submitting when there are no matching species does nothing.

        unknowns = 86

        apply_button.click()  # should do nothing
        self.wait_on_species(499)
        self.assertEqual(sidebar_value_span.text, "don't know")

        measure_input.send_keys(Keys.BACK_SPACE)  # '10000'
        self.assertIn('to the 1 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 1)
        self.assertEqual(sidebar_value_span.text, '10000 mm')

        measure_input.send_keys(Keys.BACK_SPACE)  # '1000'
        self.assertIn('to the 157 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 157)
        self.assertEqual(sidebar_value_span.text, '1000 mm')

class GlossaryFunctionalTests(FunctionalTestCase):

    def test_help_start_links_to_glossary(self):
        d = self.get('/help/start/')
        e = d.find_element_by_link_text('Glossary')
        self.assertEqual(e.get_attribute('href'), '/help/glossary/')

    def test_glossary_a_page_contains_a_terms(self):
        self.get('/help/glossary/a/')
        xterms = self.css('#terms dt')
        self.assertEqual(xterms[0].text[0], 'a')
        self.assertEqual(xterms[-1].text[0], 'a')

    def test_glossary_g_page_contains_g_terms(self):
        self.get('/help/glossary/g/')
        xterms = self.css('#terms dt')
        self.assertEqual(xterms[0].text[0], 'g')
        self.assertEqual(xterms[-1].text[0], 'g')

    def test_glossary_z_page_contains_z_terms(self):
        self.get('/help/glossary/z/')
        xterms = self.css('#terms dt')
        self.assertEqual(xterms[0].text[0], 'z')
        self.assertEqual(xterms[-1].text[0], 'z')

    def test_glossary_g_page_does_not_link_to_itself(self):
         d = self.get('/help/glossary/g/')
         e = d.find_element_by_link_text('G')
         self.assertEqual(e.get_attribute('href'), None)

    def test_glossary_g_page_link_to_other_letters(self):
        d = self.get('/help/glossary/g/')
        for letter in 'ABCVWZ':  # 'X' and 'Y' currently have no terms
            e = d.find_elements_by_link_text(letter)
            self.assertTrue(len(e))

    def test_glossary_g_page_link_is_correct(self):
        d = self.get('/help/glossary/a/')
        e = d.find_element_by_link_text('G')
        self.assertEqual(e.get_attribute('href'), '/help/glossary/g/')


class SearchFunctionalTests(FunctionalTestCase):

    def test_search_results_page(self):
        self.get('/search/?q=acer')
        results = self.css('#search-results-list li')
        self.assertEqual(len(results), 10)

    def test_search_results_page_has_navigation_links(self):
        d = self.get('/search/?q=carex&page=2')
        self.assertTrue(d.find_element_by_link_text('Previous'))
        self.assertTrue(d.find_element_by_link_text('Next'))
        nav_links = d.find_elements_by_css_selector('.search-navigation a')
        self.assertTrue(len(nav_links) >= 5)

    def test_search_results_page_scientific_name_returns_first_result(self):
        self.get('/search/?q=acer%20rubrum')
        result_links = self.css('#search-results-list li a')
        self.assertTrue(len(result_links))
        self.assertEqual('Acer rubrum (red maple)', result_links[0].text)

    def test_search_results_page_common_name_finds_correct_plant(self):
        self.get('/search/?q=christmas+fern')
        result_links = self.css('#search-results-list li a')
        self.assertTrue(len(result_links))
        url_parts = result_links[0].get_attribute('href').split('/')
        species = ' '.join(url_parts[-3:-1]).capitalize()
        self.assertEqual('Polystichum acrostichoides', species)

    def _has_icon(self, url_substring):
        has_icon = False
        result_icons = self.css('#search-results-list li img')
        self.assertTrue(len(result_icons))
        for result_icon in result_icons:
            if result_icon.get_attribute('src').find(url_substring) > -1:
                has_icon = True
                break
        return has_icon

    def test_search_results_page_has_species_results(self):
        self.get('/search/?q=sapindaceae')
        self.assertTrue(self._has_icon('leaficon'))

    def test_search_results_page_has_family_results(self):
        self.get('/search/?q=sapindaceae')
        self.assertTrue(self._has_icon('familyicon'))

    def test_search_results_page_has_genus_results(self):
        self.get('/search/?q=sapindaceae')
        self.assertTrue(self._has_icon('genusicon'))

    def test_search_results_page_has_help_results(self):
        self.get('/search/?q=start')
        self.assertTrue(self._has_icon('help-icon'))

    def test_search_results_page_has_glossary_results(self):
        self.get('/search/?q=fruit')
        self.assertTrue(self._has_icon('glossary-icon'))

    def test_search_results_page_returns_no_results(self):
        self.get('/search/?q=abcd')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertEqual('No Results for abcd', heading[0].text)
        message = self.css('#main p')
        self.assertTrue(len(message))
        self.assertEqual('Please adjust your search and try again.',
                         message[0].text)

    def test_search_results_page_has_singular_heading(self):
        self.get('/search/?q=honeycomb')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text.startswith('1 Result for'))

    def test_search_results_page_heading_starts_with_page_number(self):
        self.get('/search/?q=monocot&page=2')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text.startswith('Page 2 of'))

    def test_search_results_page_previous_link_is_present(self):
        d = self.get('/search/?q=monocot&page=2')
        self.assertTrue(d.find_element_by_link_text('Previous'))

    def test_search_results_page_next_link_is_present(self):
        d = self.get('/search/?q=monocot&page=2')
        self.assertTrue(d.find_element_by_link_text('Next'))

    def test_search_results_page_heading_number_has_thousands_comma(self):
        self.get('/search/?q=monocot')  # query that returns > 1,000 results
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        results_count = heading[0].text.split(' ')[0]
        self.assertTrue(results_count.find(',') > -1)
        self.assertTrue(int(results_count.replace(',', '')) > 1000)

    def test_search_results_page_omits_navigation_links_above_limit(self):
        MAX_PAGE_LINKS = 20
        self.get('/search?q=monocot')  # query that returns > 1,000 results
        nav_links = self.css('.search-navigation li a')
        self.assertTrue(len(nav_links))
        # The number of links should equal the maximum page links: all
        # the page links minus one (the current unlinked page) plus one
        # for the Next link.
        self.assertTrue(len(nav_links) == MAX_PAGE_LINKS)

    def test_search_results_page_navigation_has_ellipsis_above_limit(self):
        self.get('/search?q=monocot')  # query that returns > 1,000 results
        nav_list_items = self.css('.search-navigation li')
        self.assertTrue(len(nav_list_items))
        ellipsis = nav_list_items[-2]
        self.assertTrue(ellipsis.text == '...')

    def test_search_results_page_query_is_in_search_box(self):
        self.get('/search/?q=acer')
        search_box = self.css('#search input[type="text"]')
        self.assertTrue(len(search_box))
        self.assertTrue(search_box[0].get_attribute('value') == 'acer')

# -*- encoding: utf-8 -*-
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
import datetime
import os
import re
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
        cls.driver.close()
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

    def test_home_page(self):
        d = self.get('/')
        self.assertEqual(
            d.title, u'Go Botany: New England Wild Flower Society')
        e = d.find_element_by_link_text('Get Started')
        self.assertTrue(e.get_attribute('href').endswith('/simple/'))

    def test_home_page_shows_one_banner_image(self):
        d = self.get('/')
        images = self.css('#banner > img')
        # All but the first of the images should be hidden. The css()
        # function returns only visible elements, so expect just one.
        self.assertEqual(len(images), 1)

    def test_groups_page(self):
        d = self.get('/simple/')
        h3 = self.css('h3')
        self.assertEqual(len(h3), 6)
        assert h3[0].text.startswith('Woody plants')
        assert h3[1].text.startswith('Aquatic plants')
        assert h3[2].text.startswith('Grass-like plants')
        assert h3[3].text.startswith('Orchids and related plants')
        assert h3[4].text.startswith('Ferns')
        assert h3[5].text.startswith('All other flowering non-woody plants')

        # Do group links get constructed correctly?
        e = d.find_element_by_link_text('My plant is in this group')
        self.assertTrue(e.get_attribute('href').endswith('/woody-plants/'))

    def test_subgroups_page(self):
        d = self.get('/ferns/')
        q = self.css('h3')
        self.assertEqual(len(q), 3)
        assert q[0].text.startswith('True ferns and moonworts')
        assert q[1].text.startswith(
            'Clubmosses and relatives, plus quillworts')
        assert q[2].text.startswith('Horsetails and scouring-rushes')
        q = d.find_elements_by_link_text('My plant is in this subgroup')
        self.assertTrue(q[0].get_attribute('href').endswith(
            '/ferns/monilophytes/'))
        self.assertTrue(q[1].get_attribute('href').endswith(
            '/ferns/lycophytes/'))
        self.assertTrue(q[2].get_attribute('href').endswith(
            '/ferns/equisetaceae/'))

    def test_copyright_contains_current_year(self):
        # If this test fails, perhaps the template containing the
        # copyright years needs to be updated.
        d = self.get('/')
        copyright = self.css('footer .copyright')[0]
        current_year = str(datetime.datetime.now().year)
        self.assertTrue(copyright.text.find(current_year) > -1)


class PlantOfTheDayFunctionalTests(FunctionalTestCase):

    def test_home_page_has_plant_of_the_day(self):
        d = self.get('/')
        potd_heading = self.css('#potd .details h4')
        assert potd_heading[0]
        assert potd_heading[0].text.startswith('Plant of the Day')

    def test_plant_of_the_day_has_linked_image(self):
        d = self.get('/')
        linked_image = self.css('#potd a img')
        assert linked_image

    def test_plant_of_the_day_has_description_excerpt(self):
        d = self.get('/')
        description = self.css('#potd .details p')
        assert description

    def test_plant_of_the_day_has_learn_more_button(self):
        d = self.get('/')
        learn_more_button = self.css('#potd .details a.learn-more')
        assert learn_more_button

    def test_plant_of_the_day_feed_exists(self):
        f1 = self.get('/plantoftheday/')
        assert f1
        h1 = self.css('h1')
        assert not h1   # Feed should not have an HTML heading. If it does,
                        # an error page is probably showing instead.
        f2 = self.get('/plantoftheday/atom.xml')
        assert f2
        assert f1 == f2


class FilterFunctionalTests(FunctionalTestCase):

    def wait_on_species(self, expected_count, seconds=5):
        """Wait for a new batch of species to be displayed."""
        self.wait_on(seconds, self.css1, 'div.plant.in-results')

        # Returning several hundred divs takes ~10 seconds, so we have
        # jQuery count the divs for us and just return the count.

        plant_div_count = self.driver.execute_script(
            "return $('div.plant.in-results').length;")
        self.assertEqual(plant_div_count, expected_count)

        # Split "9 species matched" into ["9", "species", "matched"].

        count_words = self.css1('h3 .species-count').text.split()
        count = int(count_words[0])
        self.assertEqual(count, expected_count)

    def test_multiple_choice_filters(self):

        # Does the page load and show 18 species?

        prevent_intro_overlay = '#_view=photos'
        self.get('/ferns/lycophytes/' + prevent_intro_overlay)
        self.wait_on_species(18)

        # filter on Rhode Island

        self.css1('#state_distribution a.option').click()
        with self.wait(3):
            count = self.css1('[value="Rhode Island"] + .label + .count').text
        self.assertEqual(count, '(13)')
        self.css1('[value="Rhode Island"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(13)

        # filter on wetlands

        self.css1('#habitat_general a.option').click()
        with self.wait(3):
            count = self.css1('[value="wetlands"] + .label + .count').text
        self.assertEqual(count, '(3)')
        self.css1('[value="wetlands"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(3)

        # switch from wetlands to terrestrial

        self.css1('#habitat_general a.option').click()
        count = self.css1('[value="terrestrial"] + .label + .count').text
        self.assertEqual(count, '(9)')
        self.css1('[value="terrestrial"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(9)

        # clear the New England state

        self.css1('#state_distribution .clear-filter').click()
        self.wait_on_species(14)

    def list_family_choices(self):
        menu_options = self.css('select#families option')
        texts = [option.text for option in menu_options
                 if len(option.text) > 0]
        return texts

    def list_genus_choices(self):
        menu_options = self.css('select#genera option')
        texts = [option.text for option in menu_options
                 if len(option.text) > 0]
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

        prevent_intro_overlay = '#_view=photos'
        self.get('/ferns/lycophytes/' + prevent_intro_overlay)
        self.wait_on_species(18)

        # Do the family and genus dropdowns start by displaying all options?

        self.assertEqual(self.list_genus_choices(), all_genera)
        self.assertEqual(self.list_family_choices(), all_families)

        # Try selecting a family.

        self.css1('select#families option[value="Lycopodiaceae"]').click()
        self.wait_on_species(11)
        self.assertEqual(self.list_family_choices(), all_families)
        self.assertEqual(self.list_genus_choices(), [
                u'Dendrolycopodium', u'Diphasiastrum',
                u'Lycopodiella', u'Lycopodium', u'Spinulum',
                ])

        # Clear the family.

        self.css1('#family_clear').click()
        self.assertEqual(self.list_family_choices(), all_families)
        self.assertEqual(self.list_genus_choices(), all_genera)

        # Try selecting a genus first.

        self.css1('select#genera option[value="Lycopodium"]').click()
        self.wait_on_species(2)
        self.assertEqual(self.list_family_choices(), [u'Lycopodiaceae'])
        self.assertEqual(self.list_genus_choices(), all_genera)

        # Select the one family that is now possible.

        self.css1('select#families option[value="Lycopodiaceae"]').click()
        self.wait_on_species(2)
        self.assertEqual(self.list_family_choices(), [u'Lycopodiaceae'])
        self.assertEqual(self.list_genus_choices(), [
                u'Dendrolycopodium', u'Diphasiastrum',
                u'Lycopodiella', u'Lycopodium', u'Spinulum',
                ])

        # Clear the genus, leaving the family in place.

        self.css1('#genus_clear').click()
        self.wait_on_species(11)
        self.assertEqual(self.list_family_choices(), all_families)
        self.assertEqual(self.list_genus_choices(), [
                u'Dendrolycopodium', u'Diphasiastrum',
                u'Lycopodiella', u'Lycopodium', u'Spinulum',
                ])

    def test_thumbnail_presentation(self):

        # Are different images shown upon selecting "Show photos of" choices?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .continue').click()
        e = self.css1('.plant-list div a div.plant-img-container img')
        assert '-ha-' in e.get_attribute('src')
        self.css1('#results-display #image-types').click()
        self.css1(
            '#results-display #image-types option[value="shoots"]').click()
        assert '-sh-' in e.get_attribute('src')

    def test_show_photos_menu_default_item(self):

        # Verify that "plant form" is the default menu item for lycophytes.

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .continue').click()
        e = self.css1('.plant-list div a div.plant-img-container img')
        assert '-ha-' in e.get_attribute('src')   # 'ha' = 'plant form' image
        menu_items = self.css('#results-display #image-types option')
        self.assertTrue(len(menu_items) > 0)
        for menu_item in menu_items:
            if menu_item.text == 'plant form':
                self.assertEqual('true', menu_item.get_attribute('selected'))
            else:
                self.assertEqual(None, menu_item.get_attribute('selected'))

    def test_show_photos_menu_omitted_items(self):

        # Verify that certain menu items are omitted from the "Show
        # Photos of" menu for lycophytes.

        OMITTED_ITEMS = ['flowers and fruits', 'inflorescences', 'leaves',
                         'stems']
        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .continue').click()
        for i in range(4):
            try:
                self.css1('#results-display #image-types').click()
            except Exception:
                if i == 3:
                    raise
            else:
                break
        menu_items = self.css('#results-display #image-types option')
        self.assertTrue(len(menu_items) > 0)
        for menu_item in menu_items:
            self.assertTrue(menu_item.text not in OMITTED_ITEMS)

    @unittest2.skip("Skip til we find a new place to look for missing images")
    def test_missing_image_has_placeholder_text(self):
        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .continue').click()
        e = self.css1('.plant-list div a div.plant-img-container img')
        self.css1('#results-display #image-types').click()
        self.css1(
            '#results-display #image-types option[value="branches"]').click()
        assert '-br-' in e.get_attribute('src')
        missing_images = self.css('.plant-list .plant .missing-image p')
        assert len(missing_images) > 0
        self.assertEqual('Image not available yet', missing_images[0].text)

    def test_get_more_filters(self):
        FILTERS_CSS = 'ul.option-list li'

        prevent_intro_overlay = '#_view=photos'
        self.get('/ferns/lycophytes/' + prevent_intro_overlay)
        self.wait_on_species(18)

        filters = self.css(FILTERS_CSS)
        n = len(filters)
        self.css1('#sidebar .get-more a').click()

        self.wait_on(5, self.css, '#sb-container a.get-choices-ready')
        self.css1('#sb-container a.get-choices-ready').click()

        # Hacky, pile-specific way to wait on the choices to appear:
        self.wait_on(1, self.css, 'li#spore_surface_ly')
        filters = self.css(FILTERS_CSS)
        self.assertEqual(len(filters), n + 3)

    def test_length_filter(self):
        RANGE_DIV_CSS = '.permitted_ranges'
        INPUT_METRIC_CSS = 'input[name="measure_metric"]'
        INSTRUCTIONS_CSS = '.instructions'
        FILTER_LINK_CSS = '#plant_height_rn'

        self.get(
            '/non-monocots/remaining-non-monocots/#_filters=family,genus,plant_height_rn'
            )
        self.wait_on_species(499, seconds=21)   # Big subgroup, wait longer

        self.css1(FILTER_LINK_CSS).click()
        self.wait_on(5, self.css, RANGE_DIV_CSS)

        sidebar_value_span = self.css1('#plant_height_rn .value')
        range_div = self.css1(RANGE_DIV_CSS)
        measure_input = self.css1(INPUT_METRIC_CSS)
        instructions = self.css1(INSTRUCTIONS_CSS)
        apply_button = self.css1('.apply-btn')

        self.assertIn(u' 10 mm – 15000 mm', range_div.text)
        self.assertEqual('Change the value to narrow your selection to a'
                         ' new set of matching species.', instructions.text)

        # Type in a big number and watch the number of advertised
        # matching species change with each digit.

        measure_input.send_keys('1')
        self.assertIn('to the 38 matching species', instructions.text)

        measure_input.send_keys('0')  # '10'
        self.assertIn('to the 41 matching species', instructions.text)

        measure_input.send_keys('0')  # '100'
        self.assertIn('to the 220 matching species', instructions.text)

        measure_input.send_keys('0')  # '1000'
        self.assertIn('to the 191 matching species', instructions.text)

        measure_input.send_keys('0')  # '10000'
        self.assertIn('to the 1 matching species', instructions.text)

        measure_input.send_keys('0')  # '100000'
        self.assertEqual('', instructions.text)

        # Submitting when there are no matching species does nothing.

        unknowns = 25

        apply_button.click()  # should do nothing
        self.assertEqual(sidebar_value_span.text, '')

        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys(Keys.BACK_SPACE)  # '10000'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to the 1 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 1)
        self.assertEqual(sidebar_value_span.text, '10000 mm')

        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys(Keys.BACK_SPACE)  # '1000'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to the 191 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 191)
        self.assertEqual(sidebar_value_span.text, '1000 mm')

        # Switch to cm and then m.

        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        self.css1('input[value="cm"]').click()
        range_div = self.css1(RANGE_DIV_CSS)
        self.assertIn(u' 1 cm – 1500 cm', range_div.text)
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to the 1 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 1)
        self.assertEqual(sidebar_value_span.text, '1000 cm')

        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        self.css1('input[value="m"]').click()
        range_div = self.css1(RANGE_DIV_CSS)
        self.assertIn(u' 0.01 m – 15 m', range_div.text)
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertEqual('', instructions.text)
        apply_button.click()  # should do nothing
        self.assertEqual(sidebar_value_span.text, '1000 cm')

        # Three backspaces are necessary to reduce '1000' meters down to
        # the acceptable value of '1' meter.

        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys(Keys.BACK_SPACE)  # '100'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('', instructions.text)

        measure_input.send_keys(Keys.BACK_SPACE)  # '10'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to a new set of matching species', instructions.text)

        measure_input.send_keys(Keys.BACK_SPACE)  # '1'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to the 191 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 191)
        self.assertEqual(sidebar_value_span.text, '1 m')

    def test_length_filter_display_on_page_load(self):
        self.get('/')  # to start fresh and prevent partial reload
        self.get('/non-monocots/remaining-non-monocots/'
                 '#_filters=family,genus,plant_height_rn'
                 '&plant_height_rn=5000')
        unknowns = 26

        wait = 30  # Big subgroup, wait longer
        try:
            self.wait_on_species(unknowns + 9, seconds=wait)
        except AssertionError:
            # Give it a second chance - sometimes "499 species" flashes
            # up briefly before the filtered value kicks in.
            time.sleep(5.0)
            self.wait_on_species(unknowns + 9, seconds=wait)

        sidebar_value_span = self.css1('#plant_height_rn .value')
        self.assertEqual(sidebar_value_span.text, '5000 mm')

    def test_plant_preview_popup_appears(self):
        d = self.get('/ferns/lycophytes')
        self.wait_on_species(18)
        self.css1('#intro-overlay .continue').click()
        plant_links = self.css('.plant-list .plant a')
        self.assertTrue(len(plant_links) > 0)
        link = plant_links[0]
        link.click()
        POPUP_HEADING_CSS = '#sb-player div.modal-wrap div.inner h3'
        self.wait_on(5, self.css1, POPUP_HEADING_CSS)
        heading = self.css1(POPUP_HEADING_CSS).text
        self.assertEqual('Dendrolycopodium dendroideum prickly tree-clubmoss',
                         heading)

    def test_plant_preview_popup_shows_same_image_as_page(self):

        # Verify that the initial photo for a plant preview popup is the
        # same one that is showing on the page. (If the photo is missing
        # on the page, it doesn't matter which one the popup shows first.)

        d = self.get('/ferns/lycophytes')
        self.wait_on_species(18)
        self.css1('#intro-overlay .continue').click()
        plant_links = self.css('.plant-list .plant a')
        self.assertTrue(len(plant_links) > 0)
        linked_images = self.css('.plant-list .plant a img')
        self.assertTrue(len(linked_images) > 0)
        link = plant_links[0]
        link.click()
        clicked_image = linked_images[0].get_attribute('src').split('/')[-1]
        POPUP_HEADING_CSS = '#sb-player div.modal-wrap div.inner h3'
        self.wait_on(5, self.css1, POPUP_HEADING_CSS)
        popup_images = self.css('#sb-player .img-gallery .images img')
        self.assertTrue(len(popup_images) > 0)
        popup_image = popup_images[0].get_attribute('src').split('/')[-1]
        self.assertEqual(popup_image, clicked_image)


class GlossaryFunctionalTests(FunctionalTestCase):

    def test_start_links_to_glossary(self):
        d = self.get('/start/')
        e = d.find_element_by_link_text('Glossary')
        self.assertTrue(e.get_attribute('href').endswith('/glossary/'))

    def test_glossary_a_page_contains_a_terms(self):
        self.get('/glossary/a/')
        xterms = self.css('#terms dt')
        self.assertEqual(xterms[0].text[0], 'a')
        self.assertEqual(xterms[-1].text[0], 'a')

    def test_glossary_g_page_contains_g_terms(self):
        self.get('/glossary/g/')
        xterms = self.css('#terms dt')
        self.assertEqual(xterms[0].text[0], 'g')
        self.assertEqual(xterms[-1].text[0], 'g')

    def test_glossary_z_page_contains_z_terms(self):
        self.get('/glossary/z/')
        xterms = self.css('#terms dt')
        self.assertEqual(xterms[0].text[0], 'z')
        self.assertEqual(xterms[-1].text[0], 'z')

    def test_glossary_g_page_does_not_link_to_itself(self):
         d = self.get('/glossary/g/')
         e = d.find_element_by_link_text('G')
         self.assertEqual(e.get_attribute('href'), None)

    def test_glossary_g_page_link_to_other_letters(self):
        d = self.get('/glossary/g/')
        for letter in 'ABCVWZ':  # 'X' and 'Y' currently have no terms
            e = d.find_elements_by_link_text(letter)
            self.assertTrue(len(e))

    def test_glossary_g_page_link_is_correct(self):
        d = self.get('/glossary/a/')
        e = d.find_element_by_link_text('G')
        self.assertTrue(e.get_attribute('href').endswith('/help/glossary/g/'))


class SearchFunctionalTests(FunctionalTestCase):
    def _result_links(self):
        return self.css('#search-results-list li a')

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

    def test_search_results_page_common_name_finds_correct_plant(self):
        self.get('/search/?q=christmas+fern')
        result_links = self._result_links()
        self.assertTrue(len(result_links))
        plant_found = False
        for result_link in result_links:
            url_parts = result_link.get_attribute('href').split('/')
            species = ' '.join(url_parts[-3:-1]).capitalize()
            if species == 'Polystichum acrostichoides':
                plant_found = True
                break
        self.assertTrue(plant_found)

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
        self.assertTrue(self._has_icon('leaf'))

    def test_search_results_page_has_family_results(self):
        self.get('/search/?q=sapindaceae')
        self.assertTrue(self._has_icon('family'))

    def test_search_results_page_has_genus_results(self):
        self.get('/search/?q=sapindaceae')
        self.assertTrue(self._has_icon('genus'))

    def test_search_results_page_has_help_results(self):
        self.get('/search/?q=start')
        self.assertTrue(self._has_icon('help'))

    def test_search_results_page_has_glossary_results(self):
        self.get('/search/?q=abaxial')
        self.assertTrue(self._has_icon('glossary'))

    def test_search_results_page_returns_no_results(self):
        self.get('/search/?q=abcd')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertEqual('No results for abcd', heading[0].text)
        message = self.css('#main p')
        self.assertTrue(len(message))
        self.assertEqual('Please adjust your search and try again.',
                         message[0].text)

    def test_search_results_page_has_singular_heading(self):
        query = '%22simple+key+for+plant+identification%22'   # in quotes
        self.get('/search/?q=%s' % query)   # query that returns 1 result
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text.startswith('1 result for'))

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
        self.get('/search/?q=monocot')  # query that returns > 1,000 results
        nav_links = self.css('.search-navigation li a')
        self.assertTrue(len(nav_links))
        # The number of links should equal the maximum page links: all
        # the page links minus one (the current unlinked page) plus one
        # for the Next link.
        self.assertTrue(len(nav_links) == MAX_PAGE_LINKS)

    def test_search_results_page_navigation_has_ellipsis_above_limit(self):
        self.get('/search/?q=monocot')  # query that returns > 1,000 results
        nav_list_items = self.css('.search-navigation li')
        self.assertTrue(len(nav_list_items))
        ellipsis = nav_list_items[-2]
        self.assertTrue(ellipsis.text == '...')

    def test_search_results_page_query_is_in_search_box(self):
        self.get('/search/?q=acer')
        search_box = self.css('#search input[type="text"]')
        self.assertTrue(len(search_box))
        self.assertTrue(search_box[0].get_attribute('value') == 'acer')

    def test_search_results_page_result_titles_are_not_excerpted(self):
        self.get('/search/?q=virginica')
        result_links = self._result_links()
        self.assertTrue(len(result_links))
        for link in result_links:
            self.assertTrue(link.text.find('...') == -1)

    def test_search_results_page_document_excerpts_ignore_marked_text(self):
        # Verify that search result document excerpts for species pages
        # no longer show text that is marked to be ignored, in this case
        # a series of repeating scientific names.
        self.get('/search/?q=rhexia+virginica')
        result_document_excerpts = self.css('#search-results-list li p')
        self.assertTrue(len(result_document_excerpts))
        species_page_excerpt = result_document_excerpts[0].text
        text_to_be_ignored = ('Rhexia virginica Rhexia virginica '
                              'Rhexia virginica Rhexia virginica '
                              'Rhexia virginica Rhexia virginica')
        self.assertEqual(species_page_excerpt.find(text_to_be_ignored), -1)

    def test_search_results_page_shows_some_text_to_left_of_excerpt(self):
        self.get('/search/?q=rhexia+virginica')
        result_document_excerpts = self.css('#search-results-list li p')
        self.assertTrue(len(result_document_excerpts))
        for excerpt in result_document_excerpts:
            # Rhexia should not appear right at the beginning after an
            # ellipsis, i.e., the excerpt should start with something
            # like '...Genus: Rhexia' rather than '...Rhexia'.
            self.assertTrue(excerpt.text.find('...Rhexia') == -1)
            self.assertTrue(excerpt.text.find('Rhexia') > 3)

    # Tests for search ranking.

    def test_search_results_page_scientific_name_returns_first_result(self):
        plants = [
            ('Acer rubrum', 'red maple'),
            ('Calycanthus floridus', 'eastern sweetshrub'),
            ('Halesia carolina', 'Carolina silverbell'),
            ('Magnolia virginiana', 'sweet-bay'),
            ('Vaccinium corymbosum', 'highbush blueberry')
        ]
        for scientific_name, common_names in plants:
            self.get('/search/?q=%s' % scientific_name.lower().replace(' ',
                                                                       '+'))
            result_links = self._result_links()
            self.assertTrue(len(result_links))
            self.assertEqual('%s (%s)' % (scientific_name, common_names),
                result_links[0].text)

    def test_search_results_page_common_name_returns_first_result(self):
        plants = [
            ('Ligustrum obtusifolium', 'border privet'),
            ('Matteuccia struthiopteris', 'fiddlehead fern, ostrich fern'),
            ('Nardus stricta', 'doormat grass'),
            ('Quercus rubra', 'northern red oak'),
            ('Rhus copallinum', 'winged sumac')
        ]
        for scientific_name, common_names in plants:
            common_name = common_names.split(',')[0]
            self.get('/search/?q=%s' % common_name.lower().replace(' ', '+'))
            result_links = self._result_links()
            self.assertTrue(len(result_links))
            self.assertEqual('%s (%s)' % (scientific_name, common_names),
                result_links[0].text)

    def test_search_results_page_family_returns_first_result(self):
        families = ['Azollaceae (mosquito fern family)',
                    'Equisetaceae (horsetail family)',
                    'Isoetaceae (quillwort family)',
                    'Marsileaceae (pepperwort family)',
                    'Salviniaceae (watermoss family)']
        for family in families:
            self.get('/search/?q=%s' % family.split(' ')[0].lower())
            result_links = self._result_links()
            self.assertTrue(len(result_links))
            self.assertEqual('Family: %s' % family, result_links[0].text)

    @unittest2.skip('TODO: can John fix?')
    def test_search_results_page_genus_returns_first_result(self):
        genera = ['Claytonia (spring-beauty)',
                  'Echinochloa (barnyard grass)',
                  'Koeleria (Koeler\'s grass)',
                  'Panicum (warty panicgrass)',
                  'Saponaria (soapwort)',
                  'Verbascum (mullein)']
        for genus in genera:
            self.get('/search/?q=%s' % genus.split(' ')[0].lower())
            result_links = self._result_links()
            self.assertTrue(len(result_links))
            self.assertEqual('Genus: %s' % genus, result_links[0].text)

    # TODO: Add a test for genus common names if they become available.

    def test_search_results_page_glossary_term_returns_first_result(self):
        terms = ['acuminate', 'dichasial cyme', 'joint',
                 #'perigynium', # Why does this one still fail?
                 'terminal', 'woody']
        for term in terms:
            self.get('/search/?q=%s' % term.lower())
            result_links = self._result_links()
            self.assertTrue(len(result_links))
            self.assertEqual('Glossary: %s' % term[0].upper(),
                             result_links[0].text)

    # TODO: Add tests for plant groups and subgroups once they are
    # properly added (with any relevant friendly-title processing) to the
    # search indexes. (There is an upcoming user story for this.)

    # TODO: explore searching species names enclosed in quotes.
    # Maybe want to try and detect and search this way behind the
    # scenes if we can't reliably rank them first without quotes?

    # TODO: Test searching on synonyms.
    # Example:
    # q=saxifraga+pensylvanica
    # Returns:
    #Micranthes pensylvanica (swamp small-flowered-saxifrage)
    #Micranthes virginiensis (early small-flowered-saxifrage) 

    #####
    # Tests to confirm that various searches return Simple Key pages:
    # - Group page (aka Level 1 page: the list of plant groups)
    # - Subgroup page (aka Level 2 page: a list of plant subgroups for
    #   a group)
    # - Results page (aka Level 3 page: the questions/results page for
    #   a plant subgroup)
    #####

    def _is_page_found(self, result_links, page_title_text):
        is_page_found = False
        for link in result_links:
            if link.text.find(page_title_text) > -1:
                is_page_found = True
                break
        return is_page_found

    def _is_group_page_found(self, result_links):
        return self._is_page_found(result_links,
                                   'Simple Key for Plant Identification')

    def _is_subgroup_page_found(self, result_links, group_name):
        return self._is_page_found(result_links,
                                   '%s: Simple Key' % group_name)

    def _is_results_page_found(self, result_links, group_name, subgroup_name):
        return self._is_page_found(
            result_links, '%s: %s: Simple Key' % (subgroup_name, group_name))

    # Search on site feature name "Simple Key"

    def test_search_results_have_simple_key_pages(self):
        self.get('/search/?q=simple%20key')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 2)
        results_with_simple_key_in_title = []
        for link in result_links:
            if link.text.find('Simple Key') > -1:
                results_with_simple_key_in_title.append(link)
        # There should be at least three pages with Simple Key in the
        # title: the initial groups list page, any of the subgroups list
        # pages, and any of the subgroup results pages.
        self.assertTrue(len(results_with_simple_key_in_title) > 2)


    # Search on main heading of plant group or subgroup pages

    def test_search_results_group_page_main_heading(self):
        self.get('/search/?q=which%20group')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_subgroup_page_main_heading(self):
        self.get('/search/?q=these%20subgroups')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 5)
        self.assertTrue(self._is_subgroup_page_found(result_links,
                                                     'Woody Plants'))

    # Search on plant group or subgroup "friendly title"

    def test_search_results_have_group_page_for_friendly_title(self):
        self.get('/search/?q=woody%20plants')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_have_subgroup_page_for_friendly_title(self):
        self.get('/search/?q=woody%20broad-leaved%20plants')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_subgroup_page_found(result_links,
                                                     'Woody Plants'))

    # Search on portion of plant group or subgroup "friendly name"

    def test_search_results_have_group_page_for_friendly_name(self):
        self.get('/search/?q=lianas')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_have_subgroup_page_for_friendly_name(self):
        self.get('/search/?q=aroids')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_subgroup_page_found(
            result_links, 'Orchids and related plants'))

    # Search on portion of plant group or subgroup key characteristics
    # or exceptions text

    def test_search_results_have_group_page_for_key_characteristics(self):
        self.get('/search/?q=bark')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_have_subgroup_page_for_key_characteristics(self):
        self.get('/search/?q=%22sedges%20have%20edges%22')   # quoted query
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_subgroup_page_found(result_links,
                                                     'Grass-like plants'))

    def test_search_results_have_group_page_for_exceptions(self):
        self.get('/search/?q=showy%20flowers')   # Grass-like plants
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_have_subgroup_page_for_exceptions(self):
        self.get('/search/?q=curly%20stems')   # Horsetails
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_subgroup_page_found(result_links, 'Ferns'))

    # Search on plant scientific name

    def test_search_results_contain_results_page_for_scientific_name(self):
        self.get('/search/?q=dendrolycopodium%20dendroideum')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_results_page_found(
            result_links, 'Ferns',
            'Clubmosses and relatives, plus quillworts'))

    # Search on plant common name

    def test_search_results_contain_results_page_for_common_name(self):
        self.get('/search/?q=prickly%20tree-clubmoss')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_results_page_found(
            result_links, 'Ferns',
            'Clubmosses and relatives, plus quillworts'))

    # Search on plant genus name

    def test_search_results_contain_results_page_for_genus_name(self):
        self.get('/search/?q=dendrolycopodium')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_results_page_found(
            result_links, 'Ferns',
            'Clubmosses and relatives, plus quillworts'))

    #####
    # Dichotomous Key search results tests
    #####

    # TODO: uncomment and enhance upon adding dkey pages to search

#    def test_search_results_contain_dichotomous_key_main_page(self):
#        self.get('/search/?q=dichotomous')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 0)
#        self.assertTrue(self._is_page_found(result_links, 'Dichotomous Key'))

#    def test_search_results_contain_dichotomous_key_group_pages(self):
#        self.get('/search/?q=group%201')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 0)
#        self.assertTrue(self._is_page_found(result_links,
#                                            'Group 1: Dichotomous Key'))

#    def test_search_results_contain_dichotomous_key_family_pages(self):
#        self.get('/search/?q=lycopodiaceae')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 0)
#        self.assertTrue(self._is_page_found(
#            result_links, 'Family Lycopodiaceae: Dichotomous Key'))

#    def test_search_results_contain_dichotomous_key_genus_pages(self):
#        self.get('/search/?q=pseudolycopodiella')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 0)
#        self.assertTrue(self._is_page_found(
#            result_links, 'Pseudolycopodiella: Dichotomous Key'))


    # Test searching miscellaneous pages around the site (about, etc.)

    def test_search_results_contain_about_page(self):
        self.get('/search/?q=flora')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links, 'About Go Botany'))

    def test_search_results_contain_getting_started_page(self):
        self.get('/search/?q=get%20started')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links,
            'Getting Started with the Simple Key'))

    def test_search_results_contain_advanced_map_page(self):
        self.get('/search/?q=advanced%20map')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links,
            'Advanced Map to Groups'))

    def test_search_results_contain_video_help_topics_page(self):
        self.get('/search/?q=video%20help')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links,
            'Video Help Topics'))

    def test_search_results_contain_privacy_policy_page(self):
        self.get('/search/?q=privacy')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links, 'Privacy Policy'))

    def test_search_results_contain_terms_of_use_page(self):
        self.get('/search/?q=terms')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links, 'Terms of Use'))

    def test_search_results_contain_teaching_page(self):
        self.get('/search/?q=teaching')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links, 'Teaching'))


class SearchSuggestionsFunctionalTests(FunctionalTestCase):
    SEARCH_INPUT_CSS = '#search input'
    SEARCH_MENU_CSS = '#search .menu:not(.hidden)'
    SEARCH_SUGGESTIONS_CSS = '#search .menu li'

    def test_search_suggestions_menu_appears_on_home_page(self):
        self.get('/')
        search_input = self.css1(self.SEARCH_INPUT_CSS)
        search_input.send_keys('a')
        # Verify that the menu becomes visible.
        self.wait_on(5, self.css1, self.SEARCH_MENU_CSS)
        menu = self.css1(self.SEARCH_MENU_CSS)
        self.assertTrue(menu)
        # Verify that the menu contains suggestions.
        suggestions = self.css(self.SEARCH_SUGGESTIONS_CSS)
        self.assertTrue(len(suggestions) == 10)

    # TODO: test that the menu appears on other pages besides Home

    def _get_suggestions(self, query, compare_exact=True):
        search_input = self.css1(self.SEARCH_INPUT_CSS)
        search_input.click()
        search_input.clear()

        if compare_exact:
            search_input.send_keys(query)
        else:
            # Enter all but the last letter of the query string because we
            # exclude exact matches from the suggestions list. For example,
            # by excluding the last letter, we can check that typing 'dogwoo'
            # returns 'dogwood' as a suggestion.
            search_input.send_keys(query[:-1])

        menu = None
        try:
            # Wait for the menu. In the case of no suggestions at all,
            # the menu will disappear after briefly appearing as the
            # first few characters of the suggestion are keyed in.
            self.wait_on(1, self.css1, self.SEARCH_MENU_CSS)
            menu = self.css1(self.SEARCH_MENU_CSS)
        except NoSuchElementException:
            pass

        if menu:
            # Wait until the suggestions menu is finished updating, to avoid
            # "stale" elements that cannot be examined.
            MAX_TRIES = 50   # prevent infinite loop if no suggestions
            suggestion_items = []
            tries = 0
            while suggestion_items == [] and tries < MAX_TRIES:
                suggestion_list_items = self.css(self.SEARCH_SUGGESTIONS_CSS)
                try:
                    # Try getting all the items' text, which will trigger
                    # an exception if any of them are stale.
                    suggestion_items = [item.text
                                        for item in suggestion_list_items]
                    tries += 1
                except StaleElementReferenceException:
                    pass

        return suggestion_items

    def _suggestion_exists(self, query):
        # Report whether a given query string has the potential to appear
        # in the suggestions menu.
        suggestions = self._get_suggestions(query, compare_exact=False)
        suggestion_exists = False
        for suggestion in suggestions:
            if suggestion == query:
                suggestion_exists = True
                break
        if not suggestion_exists:
            print 'Search suggestion does not exist: ', query

        return suggestion_exists

    def _suggestions_found(self, test_suggestions):
        suggestions_found = []
        for test_suggestion in test_suggestions:
            self.get('/')
            if self._suggestion_exists(test_suggestion):
                suggestions_found.append(test_suggestion)
        return sorted(suggestions_found)

    # Tests for names and words from around the core models

    def test_family_scientific_name_suggestions_exist(self):
        SUGGESTIONS = ['sapindaceae', 'adoxaceae']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    # TODO when data available: Test for plant family common name

    def test_genus_scientific_name_suggestions_exist(self):
        SUGGESTIONS = ['acer', 'viburnum']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    # TODO when data available: Test for genus common name

    def test_plant_scientific_name_suggestions_exist(self):
        SUGGESTIONS = ['acer rubrum', 'viburnum acerifolium']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_plant_common_name_suggestions_exist(self):
        SUGGESTIONS = ['red maple', 'maple-leaved viburnum']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_plant_synonym_suggestions_exist(self):
        SUGGESTIONS = ['acer violaceum', 'negundo aceroides ssp. violaceum']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_plant_group_suggestions_exist(self):
        SUGGESTIONS = ['woody plants', 'ferns']   # PileGroup names
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_plant_subgroup_suggestions_exist(self):
        SUGGESTIONS = ['woody gymnosperms', 'lycophytes']   # Pile names
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_glossary_term_suggestions_exist(self):
        SUGGESTIONS = ['acuminate', 'pinnately compound']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_character_friendly_name_suggestions_exist(self):
        SUGGESTIONS = ['hairs on underside of leaf blade', 'seed length']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    # Test for the name of the Simple Key feature

    def test_simple_key_feature_name_suggestions_exist(self):
        SUGGESTIONS = ['simple key', 'plant identification']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    # Tests for each of the Simple Key plant groups

    def test_simple_key_woody_plants_suggestions_exist(self):
        SUGGESTIONS = ['woody plants', 'trees', 'shrubs', 'sub-shrubs',
                       'lianas']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_aquatic_plants_suggestions_exist(self):
        SUGGESTIONS = ['aquatic plants']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_grasslike_plants_suggestions_exist(self):
        SUGGESTIONS = ['grass-like plants', 'grasses', 'sedges',
                       'narrow leaves']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_orchids_and_related_plants_suggestions_exist(self):
        SUGGESTIONS = ['orchids', 'lilies', 'irises', 'aroids']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_ferns_suggestions_exist(self):
        SUGGESTIONS = ['ferns', 'horsetails', 'quillworts']
        # The suggestion 'lycopods' is in the database, but happens to not
        # come up due many other suggestions that begin with 'lycopod',
        # so excluding here.
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_other_flowering_plants_suggestions_exist(self):
        SUGGESTIONS = ['flowering dicots']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    # Tests for each of the Simple Key plant subgroups

    def test_simple_key_angiosperms_suggestions_exist(self):
        SUGGESTIONS = ['woody broad-leaved plants']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_gymnosperms_suggestions_exist(self):
        SUGGESTIONS = ['woody needle-leaved plants']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_non_thalloid_aquatic_suggestions_exist(self):
        SUGGESTIONS = ['water plants', 'milfoils', 'watershields',
                       'bladderworts', 'submerged plants']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_thalloid_aquatic_suggestions_exist(self):
        SUGGESTIONS = ['tiny water plants', 'duckweeds']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_sedges_suggestions_exist(self):
        SUGGESTIONS = ['sedges']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_true_grasses_suggestions_exist(self):
        SUGGESTIONS = ['true grasses', 'poaceae']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_remaining_graminoids_suggestions_exist(self):
        SUGGESTIONS = ['grass-like plants', 'bulrushes', 'rushes',
                       'cat-tails', 'narrow-leaved plants']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_orchids_suggestions_exist(self):
        SUGGESTIONS = ['orchids']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_non_orchid_monocots_suggestions_exist(self):
        SUGGESTIONS = ['irises', 'lilies', 'aroids', 'monocots']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_true_ferns_suggestions_exist(self):
        SUGGESTIONS = [
            'true ferns', 'ferns', 'moonworts',] #'adder\'s-tongues']
            # TODO: Enable "adder's-tongues" above upon a future possible
            # bug fix: changing the CSV data so the quote character is a
            # plain straight quote. 
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_lycophytes_suggestions_exist(self):
        SUGGESTIONS = ['clubmosses', 'quillworts']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_equisetaceae_suggestions_exist(self):
        SUGGESTIONS = ['horsetails', 'scouring-rushes']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_composites_suggestions_exist(self):
        SUGGESTIONS = ['daisies', 'goldenrods', 'aster family plants']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    def test_simple_key_remaining_non_monocots_suggestions_exist(self):
        SUGGESTIONS = ['flowering dicots']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    # Test for the 'generic' portion of common names, i.e, 'dogwood'
    # from a common name like 'silky dogwood'

    @unittest2.skip('TODO: John, is this broken, or did data change?')
    def test_generic_common_name_suggestions_exist(self):
        SUGGESTIONS = ['ground-cedar', 'spleenwort', 'spruce', 'juniper',
                       'bellwort', 'dogwood', 'american-aster', 'thistle',
                       'phlox', 'barren-strawberry']
        self.assertEqual(self._suggestions_found(SUGGESTIONS),
                         sorted(SUGGESTIONS))

    # Verify that exact matches are excluded, i.e., a suggestion for the
    # full string typed will not appear

    def test_exact_matches_are_excluded(self):
        queries = ['dogwood', 'viburnum']
        self.get('/')
        for query in queries:
            suggestions = self._get_suggestions(query)
            self.assertFalse(query in suggestions)

    @unittest2.skip('TODO: John should look at this')
    def test_suggestions_can_also_match_anywhere_in_string(self):
        # Verify that although we first try matching suggestions that
        # start with the query, if not a lot of those are found we then
        # add suggestions that match anywhere in the string.
        query = 'dogw'
        self.get('/')
        suggestions = self._get_suggestions(query)
        self.assertEqual(len(suggestions), 10)
        suggestions_that_match_at_start = [suggestion
                                           for suggestion in suggestions
                                           if suggestion.startswith(query)]
        self.assertTrue(len(suggestions_that_match_at_start) > 0)
        suggestions_that_match_anywhere = [suggestion
                                           for suggestion in suggestions
                                           if suggestion.find(query) > 0]
        self.assertTrue(len(suggestions_that_match_anywhere) > 0)


class FamilyFunctionalTests(FunctionalTestCase):

    def test_family_page(self):
        self.get('/families/lycopodiaceae/')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text == 'Family: Lycopodiaceae')
        common_name = self.css('#main h3')
        self.assertTrue(len(common_name))

    def test_family_page_has_glossarized_description(self):
        self.get('/families/lycopodiaceae/')
        description = self.css('#main p.description')
        self.assertTrue(len(description))
        self.assertTrue(len(description[0].text) > 0)
        GLOSSARY_ITEMS_CSS = '#main p.description .gloss'
        self.wait_on(5, self.css1, GLOSSARY_ITEMS_CSS)
        glossary_items = self.css(GLOSSARY_ITEMS_CSS)
        self.assertTrue(len(glossary_items))

    def test_family_page_has_example_images(self):
        self.get('/families/lycopodiaceae/')
        example_images = self.css('#main .pics a img')
        self.assertTrue(len(example_images))

    def test_family_page_has_list_of_genera(self):
        self.get('/families/lycopodiaceae/')
        genera = self.css('#main .genera li')
        self.assertTrue(len(genera))

    @unittest2.skip("Skip because this button is temporarily removed")
    def test_family_page_has_link_to_key(self):
        self.get('/families/lycopodiaceae/')
        key_link = self.css('#main a.family-genera-btn')
        self.assertTrue(len(key_link))
        self.assertTrue(key_link[0].get_attribute('href').endswith(
            '/ferns/lycophytes/#family=Lycopodiaceae'))


class GenusFunctionalTests(FunctionalTestCase):

    def test_genus_page(self):
        self.get('/genera/dendrolycopodium/')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text == 'Genus: Dendrolycopodium')
        common_name = self.css('#main h3')
        self.assertTrue(len(common_name))
        self.assertTrue(common_name[0].text == 'tree-clubmoss')

    def test_genus_page_has_glossarized_description(self):
        self.get('/genera/dendrolycopodium/')
        description = self.css('#main p.description')
        self.assertTrue(len(description))
        self.assertTrue(len(description[0].text) > 0)
        GLOSSARY_ITEMS_CSS = '#main p.description .gloss'
        self.wait_on(5, self.css1, GLOSSARY_ITEMS_CSS)
        glossary_items = self.css(GLOSSARY_ITEMS_CSS)
        self.assertTrue(len(glossary_items))

    def test_genus_page_has_example_images(self):
        self.get('/genera/dendrolycopodium/')
        example_images = self.css('#main .pics a img')
        self.assertTrue(len(example_images))

    def test_genus_page_has_family_link(self):
        self.get('/genera/dendrolycopodium/')
        family_link = self.css('#main p.family a')
        self.assertTrue(len(family_link))

    def test_genus_page_has_list_of_species(self):
        self.get('/genera/dendrolycopodium/')
        species = self.css('#main .species li')
        self.assertTrue(len(species))

    @unittest2.skip("Skip because this button is temporarily removed")
    def test_genus_page_has_link_to_key(self):
        self.get('/genera/dendrolycopodium/')
        key_link = self.css('#main a.genus-species-btn')
        self.assertTrue(len(key_link))
        self.assertTrue(key_link[0].get_attribute('href').endswith(
            '/ferns/lycophytes/#genus=Dendrolycopodium'))


class GlossarizerFunctionalTests(FunctionalTestCase):
    # Tests that verify that portions of the site have any glossary
    # terms highlighted and made into pop-up links.

    def test_glossarized_groups_page(self):
        self.get('/simple/')
        # Wait a bit for the glossarizer to finish.
        self.wait_on(5, self.css1, '.key-char .gloss')
        glossarized_key_characteristics = self.css('.key-char .gloss')
        self.assertTrue(len(glossarized_key_characteristics))
        self.wait_on(5, self.css1, '.exceptions .gloss')
        glossarized_exceptions = self.css('.exceptions .gloss')
        self.assertTrue(len(glossarized_exceptions))

    def test_glossarized_subgroups_pages(self):
        subgroup_slugs = ['ferns', 'woody-plants', 'graminoids',
                          'aquatic-plants', 'monocots', 'non-monocots']
        for slug in subgroup_slugs:
            self.get('/%s/' % slug)
            # Wait a bit for the glossarizer to finish.
            self.wait_on(5, self.css1, '.key-char .gloss')
            glossarized_key_characteristics = self.css('.key-char .gloss')
            self.assertTrue(len(glossarized_key_characteristics))
            if slug != 'ferns':  # Ferns: no words glossarized in Exceptions
                self.wait_on(5, self.css1, '.exceptions .gloss')
                glossarized_exceptions = self.css('.exceptions .gloss')
                self.assertTrue(len(glossarized_exceptions))

    def test_glossarized_species_page(self):
        self.get('/ferns/lycophytes/dendrolycopodium/dendroideum/')
        # Wait a bit for the glossarizer to finish.
        self.wait_on(5, self.css1, '#sidebar dd')
        self.assertTrue(len(self.css('#sidebar dd')))   # Lookalikes
        self.assertTrue(len(self.css('#main p')))   # Facts About
        self.assertTrue(len(self.css('#main .characteristics dl')))
        self.assertTrue(len(self.css('#main th')))  # Dist./Cons. Status



class SpeciesFunctionalTests(FunctionalTestCase):

    def _photos_have_expected_caption_format(self, species_page_url):
        # For a species page, make sure the plant photos have the expected
        # format for title/alt text that gets formatted on the fly atop 
        # each photo when it is viewed large. The text should contain a
        # title, image type, contributor, copyright holder. It can also
        # optionally have a "source" note at the end.
        REGEX_PATTERN = '.*: .*\. ~ By .*\. ~ Copyright .*\s+.( ~ .\s+)?'
        self.get(species_page_url)
        links = self.css('#species-images a')
        self.assertTrue(len(links))
        for link in links:
            title = link.get_attribute('title')
            self.assertTrue(re.match(REGEX_PATTERN, title))
        images = self.css('#species-images a img')
        self.assertTrue(len(images))
        for image in images:
            alt_text = image.get_attribute('alt')
            self.assertTrue(re.match(REGEX_PATTERN, alt_text))

    def test_species_page_photos_have_title_credit_copyright(self):
        species_page_url = '/ferns/lycophytes/dendrolycopodium/dendroideum/'
        self._photos_have_expected_caption_format(species_page_url)

    def test_species_page_photos_have_title_credit_copyright_source(self):
        # Some images on this page have "sources" specified for them.
        species_page_url = ('/species/gymnocarpium/dryopteris/')
        self._photos_have_expected_caption_format(species_page_url)

    def test_simple_key_species_page_has_breadcrumb(self):
        VALID_URLS_FOR_SPECIES = ['/ferns/monilophytes/adiantum/pedatum/',
                                  '/species/adiantum/pedatum/']
        for url in VALID_URLS_FOR_SPECIES:
            self.get(url)
            self.assertTrue(self.css1('#breadcrumb'))

    def test_non_simple_key_species_page_omits_breadcrumb(self):
        # Breadcrumb should be omitted until Full Key is implemented.
        self.get('/species/adiantum/aleuticum/')
        breadcrumb = None
        try:
            breadcrumb = self.css1('#breadcrumb')
        except NoSuchElementException:
            self.assertEqual(breadcrumb, None)
            pass

    def test_non_simple_key_species_page_has_note_about_data(self):
        # Temporarily, non-Simple-Key pages show a data disclaimer.
        self.get('/species/adiantum/aleuticum/')
        self.assertTrue(self.css1('.content .note'))


class CharacterValueImagesFunctionalTests(FunctionalTestCase):

    def _character_value_images_exist(self, page_url, character_short_name,
                                      character_value_image_ids, seconds=15):
        prevent_intro_overlay = '_view=photos'
        delimeter = '&' if ('#' in page_url) else '#'
        self.get(page_url + delimeter + prevent_intro_overlay)

        # Click on a question that has character value images.
        self.wait_on(seconds, self.css1, 'li#habitat_general')
        question_css = 'li#%s' % character_short_name
        self.wait_on(seconds, self.css1, question_css)
        self.css1(question_css).click()

        # Verify the HTML for the images expected in the working area.
        self.wait_on(seconds, self.css1, '.choices')
        for image_id in character_value_image_ids:
            image_css = '.choices img#%s' % image_id
            self.assertTrue(self.css1(image_css))

    def test_woody_angiosperms_character_value_images_exist(self):
        self._character_value_images_exist(
            '/woody-plants/woody-angiosperms/',
            'plant_habit_wa',   # Q: "Growth form?"
            ['liana', 'shrub-subshrub-wa', 'tree'])

    def test_woody_gymnosperms_character_value_images_exist(self):
        self._character_value_images_exist(
            '/woody-plants/woody-gymnosperms/',
            'habit_wg',   # Q: "Growth form?"
            ['gymnosperm-habit-shrub', 'gymnosperm-habit-tree'])

    def test_non_thalloid_aquatic_character_value_images_exist(self):
        self._character_value_images_exist(
            '/aquatic-plants/non-thalloid-aquatic/',
            'leaf_disposition_ap',   # Q: "Leaf position?"
            ['leaves-some-floating-ap', 'leaves-all-submersed-ap'])

    def test_thalloid_aquatic_character_value_images_exist(self):
        self._character_value_images_exist(
            '/aquatic-plants/thalloid-aquatic/',
            'root_presence_ta',   # Q: "Roots?"
            ['roots-none-ta', 'roots-two-or-more-ta', 'roots-one-ta'])

    def test_carex_character_value_images_exist(self):
        self._character_value_images_exist(
            '/graminoids/carex/',
            'perigynia_indument_ca',   # Q: "Fruit texture?"
            ['carex-perigynium-hairy', 'carex-perigynium-smooth'])

    def test_poaceae_character_value_images_exist(self):
        self._character_value_images_exist(
            '/graminoids/poaceae/',
            'inflorescence_branches_general_po',# Q: "Inflorescence branches?"
            ['inflo-branch-present-po', 'inflo-branch-no-po'])

    def test_remaining_graminoids_character_value_images_exist(self):
        self._character_value_images_exist(
            '/graminoids/remaining-graminoids/',
            'stem_cross-section_rg',   # Q: "Stem shape in cross-section?"
            ['stem-triangular-rg', 'stem-terete-rg'])

    def test_orchid_monocots_character_value_images_exist(self):
        self._character_value_images_exist(
            '/monocots/orchid-monocots/',
            'leaf_arrangement_om',   # Q: "Leaf arrangement?"
            ['foliage-alternate-om', 'foliage-opposite-om', 'basal-leaves-om',
             'foliage-leaves-absent-om', 'foliage-whorled-om'])

    def test_non_orchid_monocots_character_value_images_exist(self):
        self._character_value_images_exist(
            '/monocots/non-orchid-monocots/',
            'leaf_arrangement_nm',   # Q: "Leaf arrangement?"
            ['leaf-one-per-node-nm', 'leaf-two-per-node-nm',
             'leaves-basal-nm', 'leaf-three-per-node-nm'])

    def test_monilophytes_character_value_images_exist(self):
        self._character_value_images_exist(
            '/ferns/monilophytes/',
            'leaf_blade_morphology_mo',   # Q: "Leaf divisions?"
            ['fern-once-compound', # 7 Feb 2012: missing image for "lobed"
             'fern-blade-simple', 'fern-thrice-compound',
             'fern-twice-compound'])

    def test_lycophytes_character_value_images_exist(self):
        self._character_value_images_exist(
            '/ferns/lycophytes/',
            'horizontal_shoot_position_ly',   # Q: "Horizontal stem?"
            ['stem-on-surface', 'stem-subterranean'])

    def test_equisetaceae_character_value_images_exist(self):
        self._character_value_images_exist(
            '/ferns/equisetaceae/',
            'aerial_stem_habit_eq',   # Q: "Stem form?"
            ['equisetum-curved-stem', 'equisetum-straight-stem'])

    def test_composites_character_value_images_exist(self):
        self._character_value_images_exist(
            '/non-monocots/composites/',
            'leaf_arrangement_co',   # Q: "Leaf arrangement?"
            ['leaf-one-per-node-co', 'leaf-two-per-node-co',
             'leaves-basal-co', 'leaf-three-per-node-co'])

    def test_remaining_non_monocots_character_value_images_exist(self):
        self._character_value_images_exist(
            '/non-monocots/remaining-non-monocots/',
            'leaf_type_general_rn',   # Q: "Leaf type?"
            ['leaf-type-compound-rn', 'leaf-type-simple-rn'])


class PlantPreviewCharactersFunctionalTests(FunctionalTestCase):

    MIN_EXPECTED_CHARACTERS = 4   # Includes 2 common ones: Habitat, State
    GROUPS = {
        'woody-angiosperms': 'woody-plants',
        'woody-gymnosperms': 'woody-plants',
        'non-thalloid-aquatic': 'aquatic-plants',
        'thalloid-aquatic': 'aquatic-plants',
        'carex': 'graminoids',
        'poaceae': 'graminoids',
        'remaining-graminoids': 'graminoids',
        'orchid-monocots': 'monocots',
        'non-orchid-monocots': 'monocots',
        'monilophytes': 'ferns',
        'lycophytes': 'ferns',
        'equisetaceae': 'ferns',
        'composites': 'non-monocots',
        'remaining-non-monocots': 'non-monocots'
        }
    SPECIES = {
        'woody-angiosperms': ['Acer negundo', 'Ilex glabra'],
        'woody-gymnosperms': ['Abies balsamea', 'Picea rubens'],
        'non-thalloid-aquatic': ['Alisma subcordatum', 'Najas flexilis'],
        'thalloid-aquatic': ['Lemna minor', 'Spirodela polyrrhiza'],
        'carex': ['Carex albicans', 'Carex limosa'],
        'poaceae': ['Agrostis capillaris', 'Festuca rubra'],
        'remaining-graminoids': ['Bolboschoenus fluviatilis',
                                 'Juncus tenuis'],
        'orchid-monocots': ['Arethusa bulbosa', 'Isotria verticillata'],
        'non-orchid-monocots': ['Acorus americanus', 'Hypoxis hirsuta'],
        'monilophytes': ['Athyrium angustum', 'Cystopteris tenuis'],
        'lycophytes': ['Dendrolycopodium dendroideum', 'Isoetes echinospora'],
        'equisetaceae': ['Equisetum arvense', 'Equisetum palustre'],
        'composites': ['Achillea millefolium', 'Packera obovata'],
        'remaining-non-monocots': ['Abutilon theophrasti', 'Nelumbo lutea']
        }

    # Plant subgroups pages tests: the "plant preview" popups should
    # contain the expected characters.

    PLANT_PREVIEW_LIST_ITEMS_CSS = '#sb-player .details dl'
    PLANT_PREVIEW_ITEM_CHAR_NAME_CSS = '#sb-player .details dl dt'
    PLANT_PREVIEW_ITEM_CHAR_VALUE_CSS = '#sb-player .details dl dd'
    CLOSE_LINK_CSS = 'a#sb-nav-close'

    def _get_subgroup_page(self, subgroup):
        seconds = 16   # Long max. time to handle big plant subgroups
        subgroup_page_url = '/%s/%s/' % (self.GROUPS[subgroup], subgroup)
        page = self.get(subgroup_page_url)
        self.wait_on(10, self.css1, 'div.plant.in-results')
        #self.wait_on(seconds, self.css1, '#exposeMask')
        self.css1('#intro-overlay .continue').click()
        self.wait_on(seconds, self.css1, 'div.plant.in-results')
        return page

    # Test that characters are present for several species, and that the
    # characters appear to be formatted as expected.
    def _preview_popups_have_characters(self, subgroup):
        page = self._get_subgroup_page(subgroup)
        species = self.SPECIES[subgroup]
        for s in species:
            species_link = page.find_element_by_partial_link_text(s)
            time.sleep(1)   # Wait a bit for animation to finish
            species_link.click()
            self.wait_on(13, self.css1, self.PLANT_PREVIEW_LIST_ITEMS_CSS)
            list_items = self.css(self.PLANT_PREVIEW_LIST_ITEMS_CSS)
            self.assertTrue(len(list_items))
            self.assertTrue(len(list_items) >= self.MIN_EXPECTED_CHARACTERS)
            self.css1(self.CLOSE_LINK_CSS).click()

    # Test a single species, including its expected character and value.
    def _preview_popup_has_characters(self, subgroup, species,
                                      expected_name, expected_values):
        page = self._get_subgroup_page(subgroup)
        species_link = page.find_element_by_partial_link_text(species)
        time.sleep(1)   # Wait a bit for animation to finish
        species_link.click()
        self.wait_on(13, self.css1, self.PLANT_PREVIEW_LIST_ITEMS_CSS)
        list_items = self.css(self.PLANT_PREVIEW_LIST_ITEMS_CSS)
        char_names = self.css(self.PLANT_PREVIEW_ITEM_CHAR_NAME_CSS)
        char_values = self.css(self.PLANT_PREVIEW_ITEM_CHAR_VALUE_CSS)
        self.assertTrue(len(list_items))
        self.assertTrue(len(list_items) >= self.MIN_EXPECTED_CHARACTERS)
        expected_item_found = False
        for index, list_item in enumerate(list_items):
            char_name = char_names[index]
            char_value = char_values[index]
            actual_values = []
            ul_items = char_value.find_elements_by_css_selector('li')
            if len(ul_items) == 0:
                # Single character value.
                actual_values.append(char_value.text)
            else:
                # Multiple character values.
                for ul_item in ul_items:
                    actual_values.append(ul_item.text)
            if char_name.text == expected_name:
                expected_item_found = True
                for expected_value in expected_values:
                    decoded_value = expected_value.decode('utf-8')
                    self.assertIn(decoded_value, actual_values)
                break
        if not expected_item_found:
            print '%s: Expected item not found: %s %s' % (
                species, expected_name, expected_values)
        self.assertTrue(expected_item_found)
        self.css1(self.CLOSE_LINK_CSS).click()

    def test_woody_angiosperms_preview_popups_have_characters(self):
        self._preview_popups_have_characters('woody-angiosperms')

    def test_woody_gymnosperms_preview_popups_have_characters(self):
        self._preview_popups_have_characters('woody-gymnosperms')

    def test_non_thalloid_aquatic_preview_popups_have_characters(self):
        self._preview_popups_have_characters('non-thalloid-aquatic')

    def test_thalloid_aquatic_preview_popups_have_characters(self):
        self._preview_popups_have_characters('thalloid-aquatic')

    def test_carex_preview_popups_have_characters(self):
        self._preview_popups_have_characters('carex')

    def test_poaceae_preview_popups_have_characters(self):
        self._preview_popups_have_characters('poaceae')

    def test_remaining_graminoids_preview_popups_have_characters(self):
        self._preview_popups_have_characters('remaining-graminoids')

    def test_orchid_monocots_preview_popups_have_characters(self):
        self._preview_popups_have_characters('orchid-monocots')

    def test_non_orchid_monocots_preview_popups_have_characters(self):
        self._preview_popups_have_characters('non-orchid-monocots')

    def test_monilophytes_preview_popups_have_characters(self):
        self._preview_popups_have_characters('monilophytes')

    def test_lycophytes_preview_popups_have_characters(self):
        self._preview_popups_have_characters('lycophytes')

    def test_equisetaceae_preview_popups_have_characters(self):
        self._preview_popups_have_characters('equisetaceae')

    def test_composites_preview_popups_have_characters(self):
        self._preview_popups_have_characters('composites')

    def test_remaining_non_monocots_preview_popups_have_characters(self):
        self._preview_popups_have_characters('remaining-non-monocots')

    # Plant preview popups: Verify some expected characters and values.
    def test_plant_preview_popups_have_expected_values(self):
        values = [
            ('non-thalloid-aquatic', 'Elatine minima',
             'LEAF BLADE LENGTH', ['0.7–5 cm']),
            ('non-thalloid-aquatic', 'Brasenia schreberi',
             'LEAF BLADE LENGTH', ['35–135 cm']),
            ('carex', 'Carex aquatilis',
             'LEAF BLADE WIDTH', ['2.5–8 mm']),
            ('non-thalloid-aquatic', 'Elatine minima',
             'PETAL OR SEPAL NUMBER',
             ['there are three petals, sepals or tepals in the flower',
              'there are two petals, sepals or tepals in the flower']),
            ]
        for subgroup, species, expected_name, expected_values in values:
            self._preview_popup_has_characters(subgroup, species,
                                               expected_name, expected_values)

    # Species pages tests: The same "plant preview" characters should
    # appear in the Characteristics section of the page, below the
    # heading and above the expandable list of all characters.

    def _species_pages_have_characters(self, subgroup):
        species = self.SPECIES[subgroup]
        for s in species:
            species_page_url = '/species/%s/' % s.lower().replace(' ', '/')
            self.get(species_page_url)
            list_items = self.css('.characteristics dl')
            self.assertTrue(len(list_items))
            self.assertTrue(len(list_items) >= self.MIN_EXPECTED_CHARACTERS)

    def test_woody_angiosperms_species_pages_have_characters(self):
        self._species_pages_have_characters('woody-angiosperms')

    def test_woody_gymnosperms_species_pages_have_characters(self):
        self._species_pages_have_characters('woody-gymnosperms')

    def test_non_thalloid_aquatic_species_pages_have_characters(self):
        self._species_pages_have_characters('non-thalloid-aquatic')

    def test_thalloid_aquatic_species_pages_have_characters(self):
        self._species_pages_have_characters('thalloid-aquatic')

    def test_carex_species_pages_have_characters(self):
        self._species_pages_have_characters('carex')

    def test_poaceae_species_pages_have_characters(self):
        self._species_pages_have_characters('poaceae')

    def test_remaining_graminoids_species_pages_have_characters(self):
        self._species_pages_have_characters('remaining-graminoids')

    def test_orchid_monocots_species_pages_have_characters(self):
        self._species_pages_have_characters('orchid-monocots')

    def test_non_orchid_monocots_species_pages_have_characters(self):
        self._species_pages_have_characters('non-orchid-monocots')

    def test_monilophytes_species_pages_have_characters(self):
        self._species_pages_have_characters('monilophytes')

    def test_lycophytes_species_pages_have_characters(self):
        self._species_pages_have_characters('lycophytes')

    def test_equisetaceae_species_pages_have_characters(self):
        self._species_pages_have_characters('equisetaceae')

    def test_composites_species_pages_have_characters(self):
        self._species_pages_have_characters('composites')

    def test_remaining_non_monocots_species_pages_have_characters(self):
        self._species_pages_have_characters('remaining-non-monocots')

    # Verify there are no duplicate characters in the initially-visible
    # "brief" Characteristics section on the species page.
    def test_species_page_has_no_duplicate_brief_characteristics(self):
        species = ['Elatine minima', 'Eleocharis acicularis',
                   'Eleocharis robbinsii', 'Alisma subcordatum',
                   'Sagittaria cuneata', 'Utricularia intermedia']
        for s in species:
            self.get('/species/%s/' % s.replace(' ', '/').lower())
            list_items = self.css('.characteristics dt')
            character_names = []
            for list_item in list_items:
                character_name = list_item.text
                character_names.append(character_name)
            self.assertTrue(len(character_names) > 0)
            self.assertEqual(len(character_names), len(set(character_names)))


class LookalikesFunctionalTests(FunctionalTestCase):

    def test_lookalikes_are_in_search_indexes_for_many_pages(self):
        self.get('/search/?q=sometimes+confused+with')
        page_links = self.css('.search-navigation li')
        self.assertTrue(len(page_links) > 10)   # more than 100 results

    def test_species_pages_have_lookalikes(self):
        # Verify a sampling of the species expected to have lookalikes.
        SPECIES = ['Huperzia appressa', 'Lonicera dioica', 'Actaea rubra',
                   'Digitalis purpurea', 'Brachyelytrum aristosum']
        for s in SPECIES:
            url = '/species/%s/' % s.replace(' ', '/').lower()
            self.get(url)
            heading = self.css('#sidebar .lookalikes h5')
            self.assertTrue(heading)
            lookalikes = self.css('#sidebar .lookalikes dt')
            self.assertTrue(len(lookalikes) > 0)
            for lookalike in lookalikes:
                self.assertTrue(len(lookalike.text) > 0)
            notes = self.css('#sidebar .lookalikes dd')
            self.assertTrue(len(notes) > 0)
            for note in notes:
                self.assertTrue(len(note.text) > 0)

class ResultsPageStateFunctionalTests(FunctionalTestCase):

    # Tests for:
    # - restoring the results page state from a URL
    # - saving the results page state to URL and cookie
    # - "undo" of filtering choices via Back button

    def test_filters_load_with_no_hash(self):
        page = self.get('/ferns/lycophytes/')
        self.wait_on(10, self.css1, 'div.plant.in-results')
        self.css1('#intro-overlay .continue').click()
        self.assertTrue(page.find_element_by_xpath(
            '//li/a/span/span[text()="Habitat"]'))  # glossarized: extra span
        self.assertTrue(page.find_element_by_xpath(
            '//li/a/span[text()="New England state"]'))

    def test_filters_load_from_url_hash(self):
        # Although only two filters are specified on the URL hash, the
        # entire list of default filters will come up in the UI, including
        # these two hash-specified filters. This is OK now because the
        # user can no longer delete filters from the UI as they once
        # could. Actual URLs in the UI consist of the entire list of
        # default filters followed by any "Get More Choices" filters the
        # user has loaded.
        #
        # Family and genus filters are always present so do not need to
        # be included in the URL. However, they were present in the URL
        # previously, so make sure the site still properly ignores them.
        url = ('/ferns/lycophytes/#_filters=habitat_general,'
               'state_distribution,family,genus')
        page = self.get(url)
        self.wait_on(10, self.css1, 'div.plant.in-results')
        # When setting up the page from the URL hash, there is no intro 
        # overlay, so no need to wait for it as usual.
        self.assertTrue(page.find_element_by_xpath(
            '//li/a/span/span[text()="Habitat"]'))  # glossarized: extra span
        self.assertTrue(page.find_element_by_xpath(
            '//li/a/span[text()="New England state"]'))

    def test_set_family_from_url_hash(self):
        url = ('/ferns/lycophytes/#_filters=habitat_general,'
               'state_distribution&family=Isoetaceae')
        page = self.get(url)
        self.wait_on(10, self.css1, 'div.plant.in-results')
        # Verify the species are filtered after waiting a bit.
        x1 = '//span[@class="species-count" and text()="3"]'
        x2 = '//select/option[@selected="selected" and @value="Isoetaceae"]'
        self.wait_on(10, page.find_element_by_xpath, x1)
        self.wait_on(10, page.find_element_by_xpath, x2)

    def test_set_genus_from_url_hash(self):
        url = ('/ferns/lycophytes/#_filters=habitat_general,'
               'state_distribution&genus=Selaginella')
        page = self.get(url)
        self.wait_on(10, self.css1, 'div.plant.in-results')
        # Verify the species are filtered after waiting a bit.
        x1 = '//span[@class="species-count" and text()="2"]'
        x2 = '//select/option[@selected="selected" and @value="Selaginella"]'
        self.wait_on(10, page.find_element_by_xpath, x1)
        self.wait_on(10, page.find_element_by_xpath, x2)

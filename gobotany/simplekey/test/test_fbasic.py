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
        assert q[2].text.startswith('Horsetails and scouring rushes')
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
        f2 = self.get('/plantoftheday/atom.xml')
        assert f2
        assert f1 == f2


class FilterFunctionalTests(FunctionalTestCase):

    def wait_on_species(self, expected_count):
        """Wait for a new batch of species to be displayed."""
        self.wait_on(5, self.css1, 'div.plant.in-results')

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

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        self.css1('#state_distribution a.option').click()
        count = self.css1('[value="Rhode Island"] + .label + .count').text
        self.assertEqual(count, '(13)')
        self.css1('[value="Rhode Island"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(13)

        # filter on wetlands

        self.css1('#habitat_general a.option').click()
        count = self.css1('[value="wetlands"] + .label + .count').text
        self.assertEqual(count, '(3)')
        self.css1('[value="wetlands"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(3)

        # switch from wetlands to terrestrial

        self.css1('#habitat_general a.option').click()
        count = self.css1('[value="terrestrial"] + .label + .count').text
        self.assertEqual(count, '(10)')
        self.css1('[value="terrestrial"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(10)

        # clear the New England state

        self.css1('#state_distribution .clear-filter').click()
        self.wait_on_species(15)

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

    @unittest2.skip('delete if closing working area upon Apply is approved')
    def test_quickly_press_apply_twice(self):

        # Does a double tap of "apply" load species twice?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        #d.find_element_by_link_text('New England state').click()
        self.css1('#state_distribution a.option').click()

        count = self.css1('[value="Rhode Island"] + .label + .count').text
        self.assertEqual(count, '(13)')

        self.css1('[value="Rhode Island"]').click()
        self.css1('.apply-btn').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(13)

    @unittest2.skip('delete if closing working area upon Apply is approved')
    def test_quickly_press_apply_and_clear(self):

        # Does pressing the "apply" button and a "clear" link
        # simultaneously result in the result being updated twice?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)

        # filter on Rhode Island

        self.css1('#state_distribution a.option').click()

        # Pausing to fetch the item count makes this test stable, so:
        count = self.css1('[value="Rhode Island"] + .label + .count').text
        self.assertEqual(count, '(13)')

        self.css1('[value="Rhode Island"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(13)

        # filter on bogs

        self.css1('#habitat_general a.option').click()
        self.css1('[value="aquatic"]').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(3)

        # clear the New England state AND press "apply" again

        self.css1('#state_distribution .clear-filter').click()
        self.css1('.apply-btn').click()
        self.wait_on_species(3)

    def test_thumbnail_presentation(self):

        # Are different images shown upon selecting "Show photos of" choices?

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .get-started').click()
        e = self.css1('.plant-list div a div.img-container img')
        assert '-ha-' in e.get_attribute('src')
        self.css1('#results-display .dijitSelectLabel').click()
        self.css1('#dijit_MenuItem_2_text').click()  # 'shoots'
        assert '-sh-' in e.get_attribute('src')

    def test_show_photos_menu_default_item(self):

        # Verify that "plant form" is the default menu item for lycophytes.

        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .get-started').click()
        e = self.css1('.plant-list div a div.img-container img')
        assert '-ha-' in e.get_attribute('src')   # 'ha' = 'plant form' image
        default_item = self.css1('#results-display .dijitSelectLabel').text
        self.assertEqual('plant form', default_item)

    def test_show_photos_menu_omitted_items(self):

        # Verify that certain menu items are omitted from the "Show
        # Photos of" menu for lycophytes.

        OMITTED_ITEMS = ['flowers and fruits', 'inflorescences', 'leaves',
                         'stems']
        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .get-started').click()
        self.css1('#results-display .dijitSelectLabel').click()
        menu_items = self.css('#image-type-selector_menu .dijitMenuItemLabel')
        for menu_item in menu_items:
            self.assertTrue(menu_item.text not in OMITTED_ITEMS)

    def test_missing_image_has_placeholder_text(self):
        self.get('/ferns/lycophytes/')
        self.wait_on_species(18)
        self.css1('#intro-overlay .get-started').click()
        e = self.css1('.plant-list div a div.img-container img')
        self.css1('#results-display .dijitSelectLabel').click()
        self.css1('#dijit_MenuItem_0_text').click()  # 'branches'
        assert '-br-' in e.get_attribute('src')
        missing_images = self.css('.plant-list .plant .missing-image p')
        assert len(missing_images) > 0
        self.assertEqual('Image not available yet', missing_images[0].text)

    def test_get_more_filters(self):
        FILTERS_CSS = 'ul.option-list li'

        self.get('/ferns/lycophytes/')
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
        FILTER_LINK_CSS = '#plant_height_rn a.option'

        self.get(
            '/non-monocots/remaining-non-monocots/#_filters=family,genus,plant_height_rn&_visible=plant_height_rn'
            )
        self.wait_on_species(499)
        sidebar_value_span = self.css1('#plant_height_rn .value')
        range_div = self.css1(RANGE_DIV_CSS)
        measure_input = self.css1(INPUT_METRIC_CSS)
        instructions = self.css1(INSTRUCTIONS_CSS)
        apply_button = self.css1('.apply-btn')

        self.assertIn(u' 10 mm – 15000 mm', range_div.text)
        self.assertEqual('', instructions.text)

        # Type in a big number and watch the number of advertised
        # matching species change with each digit.

        measure_input.send_keys('1')
        self.assertEqual('', instructions.text)

        measure_input.send_keys('0')  # '10'
        self.assertIn('to the 3 matching species', instructions.text)

        measure_input.send_keys('0')  # '100'
        self.assertIn('to the 175 matching species', instructions.text)

        measure_input.send_keys('0')  # '1000'
        self.assertIn('to the 157 matching species', instructions.text)

        measure_input.send_keys('0')  # '10000'
        self.assertIn('to the 1 matching species', instructions.text)

        measure_input.send_keys('0')  # '100000'
        self.assertEqual('', instructions.text)

        # Submitting when there are no matching species does nothing.

        unknowns = 86

        apply_button.click()  # should do nothing
        self.wait_on_species(499)
        self.assertEqual(sidebar_value_span.text, "don't know")

        # Open the working area again and set the metric length back to
        # what it was before the working area closed.
        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys('100000')

        measure_input.send_keys(Keys.BACK_SPACE)  # '10000'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to the 1 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 1)
        self.assertEqual(sidebar_value_span.text, '10000.0 mm')

        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys('10000')
        measure_input.send_keys(Keys.BACK_SPACE)  # '1000'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to the 157 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 157)
        self.assertEqual(sidebar_value_span.text, '1000.0 mm')

        # Switch to cm and then m.

        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys('1000')
        self.css1('input[value="cm"]').click()
        range_div = self.css1(RANGE_DIV_CSS)
        self.assertIn(u' 1 cm – 1500 cm', range_div.text)
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertIn('to the 1 matching species', instructions.text)
        apply_button.click()
        self.wait_on_species(unknowns + 1)
        self.assertEqual(sidebar_value_span.text, '1000.0 cm')

        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys('1000')
        self.css1('input[value="m"]').click()
        range_div = self.css1(RANGE_DIV_CSS)
        self.assertIn(u' 0.01 m – 15 m', range_div.text)
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertEqual('', instructions.text)
        apply_button.click()  # should do nothing
        self.wait_on_species(unknowns + 1)
        self.assertEqual(sidebar_value_span.text, '1000.0 cm')

        self.css1(FILTER_LINK_CSS).click()
        measure_input = self.css1(INPUT_METRIC_CSS)
        measure_input.send_keys('1000')
        self.css1('input[value="m"]').click()

        # Two backspaces are necessary to reduce '1000' meters down to
        # the acceptable value of '10' meters.

        measure_input.send_keys(Keys.BACK_SPACE)  # '100'
        instructions = self.css1(INSTRUCTIONS_CSS)
        self.assertEqual('', instructions.text)

        measure_input.send_keys(Keys.BACK_SPACE)  # '10'
        self.assertIn('to the 1 matching species', instructions.text)
        apply_button.click()  # should do nothing
        self.wait_on_species(unknowns + 1)
        self.assertEqual(sidebar_value_span.text, '10.00 m')

    def test_length_filter_display_on_page_load(self):
        self.get('/')  # to start fresh and prevent partial reload
        self.get('/non-monocots/remaining-non-monocots/'
                 '#_filters=family,genus,plant_height_rn'
                 '&_visible=plant_height_rn'
                 '&plant_height_rn=5000')
        unknowns = 86
        self.wait_on_species(unknowns + 8)
        sidebar_value_span = self.css1('#plant_height_rn .value')
        self.assertEqual(sidebar_value_span.text, '5000.0 mm')

    def test_plant_preview_popup_appears(self):
        d = self.get('/ferns/lycophytes')
        self.wait_on_species(18)
        self.css1('#intro-overlay .get-started').click()
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
        self.css1('#intro-overlay .get-started').click()
        plant_links = self.css('.plant-list .plant a')
        self.assertTrue(len(plant_links) > 0)
        linked_images = self.css('.plant-list .plant a img')
        self.assertTrue(len(linked_images) > 0)
        link = plant_links[0]
        link.click()
        clicked_image = linked_images[0].get_attribute('src')
        clicked_image = clicked_image[0:clicked_image.find('_jpg_')]
        POPUP_HEADING_CSS = '#sb-player div.modal-wrap div.inner h3'
        self.wait_on(5, self.css1, POPUP_HEADING_CSS)
        popup_images = self.css('#sb-player .img-gallery .images img')
        self.assertTrue(len(popup_images) > 0)
        popup_image = popup_images[0].get_attribute('src')
        popup_image = popup_image[0:popup_image.find('_jpg_')]
        self.assertEqual(popup_image, clicked_image)


class GlossaryFunctionalTests(FunctionalTestCase):

    def test_help_start_links_to_glossary(self):
        d = self.get('/help/start/')
        e = d.find_element_by_link_text('Glossary')
        self.assertTrue(e.get_attribute('href').endswith('/help/glossary/'))

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
        self.assertEqual('No Results for abcd', heading[0].text)
        message = self.css('#main p')
        self.assertTrue(len(message))
        self.assertEqual('Please adjust your search and try again.',
                         message[0].text)

    def test_search_results_page_has_singular_heading(self):
        self.get('/search/?q=carved+quillwort')
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
        families = ['Azollaceae', 'Equisetaceae', 'Isoetaceae',
                    'Marsileaceae', 'Salviniaceae']
        for family in families:
            self.get('/search/?q=%s' % family.lower())
            result_links = self._result_links()
            self.assertTrue(len(result_links))
            self.assertEqual('Family: %s' % family, result_links[0].text)

    # TODO: Add a test for family common names when they become available.

    def test_search_results_page_genus_returns_first_result(self):
        genera = ['Claytonia', 'Echinochloa', 'Koeleria', 'Panicum',
                  'Saponaria', 'Verbascum']
        for genus in genera:
            self.get('/search/?q=%s' % genus.lower())
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
    # - Keying page (aka Level 3 page: the keying/results page for a
    #   plant subgroup)
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

    def _is_keying_page_found(self, result_links, group_name, subgroup_name):
        return self._is_page_found(
            result_links, '%s: %s: Simple Key' % (group_name, subgroup_name))

    # Search on site feature name "Simple Key"

#    def test_search_results_have_simple_key_pages(self):
#        self.get('/search/?q=simple%20key')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 2)
#        results_with_simple_key_in_title = []
#        for link in result_links:
#            if link.text.find('Simple Key') > -1:
#                results_with_simple_key_in_title.append(link)
#        # There should be at least three pages with Simple Key in the
#        # title: the initial groups list page, any of the subgroups list
#        # pages, and any of the subgroup keying/results pages.
#        self.assertTrue(len(resuts_with_simple_key_in_title) > 2)


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
        self.get('/search/?q=trees')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_have_subgroup_page_for_friendly_name(self):
        self.get('/search/?q=bulrushes')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_subgroup_page_found(result_links,
                                                     'Grass-like plants'))

    # Search on portion of plant group or subgroup key characteristics
    # or exceptions text

    def test_search_results_have_group_page_for_key_characteristics(self):
        self.get('/search/?q=bark')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_have_subgroup_page_for_key_characteristics(self):
        self.get('/search/?q=sedges%20have%20edges')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_subgroup_page_found(result_links,
                                                     'Grass-like plants'))

    def test_search_results_have_group_page_for_exceptions(self):
        self.get('/search/?q=dissected%20leaves')   # Ferns
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_group_page_found(result_links))

    def test_search_results_have_subgroup_page_for_exceptions(self):
        self.get('/search/?q=curly%20stems')   # Horsetails
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_subgroup_page_found(result_links, 'Ferns'))

    # Search on plant scientific name

#    def test_search_results_have_keying_page_for_scientific_name(self):
#        self.get('/search/?q=dendrolycopodium%20dendroideum')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 0)
#        self.assertTrue(self._is_keying_page_found(
#            result_links, 'Ferns',
#            'Clubmosses and relatives, plus quillworts'))

    # Search on plant common name

#    def test_search_results_contain_results_page_for_common_name(self):
#        self.get('/search/?q=prickly%20tree-clubmoss')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 0)
#        self.assertTrue(self._is_keying_page_found(
#            result_links, 'Ferns',
#            'Clubmosses and relatives, plus quillworts'))

    # Search on plant genus name

#    def test_search_results_contain_results_page_for_genus_name(self):
#        self.get('/search/?q=dendrolycopdium')
#        result_links = self._result_links()
#        self.assertTrue(len(result_links) > 0)
#        self.assertTrue(self._is_keying_page_found(
#            result_links, 'Ferns',
#            'Clubmosses and relatives, plus quillworts'))


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
        glossary_items = self.css('#main p.description .gloss')
        self.assertTrue(len(glossary_items))

    @unittest2.skip('is this really broken or does Brandon lack the images?')
    # TODO: This test passes after import_sample, but not after
    # import_data, due to whether or not local images are available. Will
    # probably need to rearrange import scripts to fix.
    def test_family_page_has_example_images(self):
        self.get('/families/lycopodiaceae/')
        example_images = self.css('#main .pics a img')
        self.assertTrue(len(example_images))

    def test_family_page_has_list_of_genera(self):
        self.get('/families/lycopodiaceae/')
        genera = self.css('#main .genera li')
        self.assertTrue(len(genera))

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

    def test_genus_page_has_glossarized_description(self):
        self.get('/genera/dendrolycopodium/')
        description = self.css('#main p.description')
        self.assertTrue(len(description))
        self.assertTrue(len(description[0].text) > 0)
        glossary_items = self.css('#main p.description .gloss')
        self.assertTrue(len(glossary_items))

    @unittest2.skip('is this really broken or does Brandon lack the images?')
    # TODO: This test passes after import_sample, but not after
    # import_data, due to whether or not local images are available. Will
    # probably need to rearrange import scripts to fix.
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
        self.assertTrue(len(self.css('#sidebar dd')))
        self.assertTrue(len(self.css('#main p')))
        self.assertTrue(len(self.css('#main li')))
        self.assertTrue(len(self.css('#main th')))



class SpeciesFunctionalTests(FunctionalTestCase):

    def test_species_page_photos_have_title_and_credit(self):
        REGEX_PATTERN = '^.*: .*\. Photo by .*\. Copyright .*\s+NEWFS.'
        self.get('/ferns/lycophytes/dendrolycopodium/dendroideum/')
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

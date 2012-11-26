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
import os
import re
import time
import unittest
from contextlib import contextmanager
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException
    )
from selenium.webdriver.common.keys import Keys

class FunctionalTestCase(unittest.TestCase):

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
        return [ e for e in elements if self.is_displayed(e) ]

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

    def is_displayed(self, element):
        """Return whether an element is visible on the page."""
        try:
            return element.is_displayed()
        except StaleElementReferenceException:
            return False

    def hide_django_debug_toolbar(self):
        # Dismiss the Django Debug toolbar if it is visible.
        try:
            toolbar = self.css1('#djDebugToolbar')
        except NoSuchElementException:
            pass
        else:
            if self.is_displayed(toolbar):
                self.css1('#djHideToolBarButton').click()

class BasicFunctionalTests(FunctionalTestCase):

    # Tests

    def test_home_page_shows_one_banner_image(self):
        self.get('/')
        images = self.css('#banner > img')
        # All but the first of the images should be hidden. The css()
        # function returns only visible elements, so expect just one.
        self.assertEqual(len(images), 1)


class NavigationFunctionalTests(FunctionalTestCase):

    # Header navigation items: current section highlight

    def _is_nav_item_highlighted(self, page_path, css_selector):
        self.get(page_path)
        li = self.css1(css_selector)
        image = li.value_of_css_property('background-image')
        valid = re.compile(r'^url\(.*active-nav.*png\)$')
        return True if valid.match(str(image)) else False

    def test_header_home_item_highlighted(self):
        self.assertTrue(self._is_nav_item_highlighted('/', 'header li.home'))

    def test_header_simple_key_item_highlighted(self):
        self.assertTrue(self._is_nav_item_highlighted(
            '/simple/',
            'header li.simple a')   # remove 'a' upon moving to 'site' app
            )

    def test_header_simple_key_item_highlighted_within_section(self):
        self.assertTrue(self._is_nav_item_highlighted(
            '/simple/woody-plants/',
            'header li.simple a')   # remove 'a' upon moving to 'site' app
            )

    def test_header_plantshare_item_highlighted(self):
        self.assertTrue(
            self._is_nav_item_highlighted('/ps/', 'header li.plantshare'))

    def test_header_plantshare_item_highlighted_within_section(self):
        self.assertTrue(
            self._is_nav_item_highlighted('/ps/accounts/register/',
                                          'header li.plantshare'))

    def test_header_full_key_item_highlighted(self):
        self.assertTrue(self._is_nav_item_highlighted(
            '/full/',
            'header li.full a')   # remove 'a' upon moving to 'site' app
            )

    def test_header_full_key_item_highlighted_within_section(self):
        self.assertTrue(self._is_nav_item_highlighted(
            '/full/woody-plants/',
            'header li.full a')   # remove 'a' upon moving to 'site' app
            )

    @unittest.skip('Skip for now: page returns error')
    def test_header_dkey_item_highlighted(self):
        self.assertTrue(
            self._is_nav_item_highlighted('/dkey/', 'header li.dkey'))

    @unittest.skip('Skip for now: page returns error')
    def test_header_dkey_item_highlighted_within_section(self):
        self.assertTrue(
            self._is_nav_item_highlighted('/dkey/Key-to-the-Families/',
                                          'header li.dkey'))

    def test_header_teaching_item_highlighted(self):
        self.assertTrue(
            self._is_nav_item_highlighted('/teaching/',
                                          'header li.teaching'))

    def test_header_about_item_highlighted(self):
        self.assertTrue(
            self._is_nav_item_highlighted('/about/', 'header li.about'))

    def test_header_about_item_highlighted_within_section(self):
        self.assertTrue(
            self._is_nav_item_highlighted('/start/', 'header li.about'))



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

    def test_missing_image_has_placeholder_text(self):
        self.get('/aquatic-plants/non-thalloid-aquatic/')
        self.wait_on_species(52)
        self.css1('#intro-overlay .continue').click()
        self.css1(
            '#results-display #image-types option[value="flowers"]').click()
        # Verify that an image is present for the first visible plant.
        e = self.css1(
            '.plant-list .plant img[alt="Alisma subcordatum: flowers 1"]')
        assert '-fl-' in e.get_attribute('src')
        # Verify that there are, in fact, some plants in this subgroup
        # which do not yet have images for this image type.
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
        self.wait_on_species(500, seconds=21)   # Big subgroup, wait longer

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

        unknowns = 26

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
        unknowns = 27

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
        self.hide_django_debug_toolbar()

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

    def test_family_page_has_glossarized_description(self):
        self.get('/families/lycopodiaceae/')
        description = self.css('#main p.description')
        self.assertTrue(len(description))
        self.assertTrue(len(description[0].text) > 0)
        GLOSSARY_ITEMS_CSS = '#main p.description .gloss'
        self.wait_on(5, self.css1, GLOSSARY_ITEMS_CSS)
        glossary_items = self.css(GLOSSARY_ITEMS_CSS)
        self.assertTrue(len(glossary_items))

    @unittest.skip("Skip because this button is temporarily removed")
    def test_family_page_has_link_to_key(self):
        self.get('/families/lycopodiaceae/')
        key_link = self.css('#main a.family-genera-btn')
        self.assertTrue(len(key_link))
        self.assertTrue(key_link[0].get_attribute('href').endswith(
            '/ferns/lycophytes/#family=Lycopodiaceae'))


class GenusFunctionalTests(FunctionalTestCase):

    def test_genus_page_has_glossarized_description(self):
        self.get('/genera/dendrolycopodium/')
        description = self.css('#main p.description')
        self.assertTrue(len(description))
        self.assertTrue(len(description[0].text) > 0)
        GLOSSARY_ITEMS_CSS = '#main p.description .gloss'
        self.wait_on(5, self.css1, GLOSSARY_ITEMS_CSS)
        glossary_items = self.css(GLOSSARY_ITEMS_CSS)
        self.assertTrue(len(glossary_items))

    @unittest.skip("Skip because this button is temporarily removed")
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
        self.hide_django_debug_toolbar()
        self.wait_on(10, self.css1, 'div.plant.in-results')
        #self.wait_on(seconds, self.css1, '#exposeMask')
        self.css1('#intro-overlay .continue').click()
        self.wait_on(seconds, self.css1, 'div.plant.in-results')
        return page

    # Test that characters are present for several species, and that the
    # characters appear to be formatted as expected.
    def _preview_popups_have_characters(self, subgroup):
        page = self._get_subgroup_page(subgroup)
        self.hide_django_debug_toolbar()
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
        self.hide_django_debug_toolbar()
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
             'LEAF BLADE LENGTH', ['0.7–5 mm']),
            ('non-thalloid-aquatic', 'Brasenia schreberi',
             'LEAF BLADE LENGTH', ['35–135 mm']),
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
            self.hide_django_debug_toolbar()
            list_items = self.css('.characteristics dt')
            character_names = []
            for list_item in list_items:
                character_name = list_item.text
                character_names.append(character_name)
            self.assertTrue(len(character_names) > 0)
            self.assertEqual(len(character_names), len(set(character_names)))


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

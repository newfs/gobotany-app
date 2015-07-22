import requests
import unittest
from django.conf import settings
from haystack.utils import Highlighter
from highlight import ExtendedHighlighter

from gobotany.libtest import FunctionalCase


class SearchTests(FunctionalCase):

    solr_available = None

    @classmethod
    def setUpClass(cls):
        super(SearchTests, cls).setUpClass()
        try:
            requests.get(settings.HAYSTACK_SOLR_URL)
        except requests.RequestException:
            cls.solr_available = False
        else:
            cls.solr_available = True

    def setUp(self):
        super(SearchTests, self).setUp()
        if not self.solr_available:
            raise unittest.SkipTest('Solr is not up and running')

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
        heading = self.css('h1')
        self.assertTrue(len(heading))
        self.assertEqual('No results for abcd', heading[0].text)
        message = self.css('#main p')
        self.assertTrue(len(message))
        self.assertEqual('Please adjust your search and try again.',
                         message[0].text)

    def test_search_results_page_has_singular_heading(self):
        query = '%22simple+key+for+plant+identification%22'   # in quotes
        self.get('/search/?q=%s' % query)   # query that returns 1 result
        heading = self.css('h1')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text.startswith('1 result for'))

    def test_search_results_page_heading_starts_with_page_number(self):
        self.get('/search/?q=monocot&page=2')
        heading = self.css('h1')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text.startswith('Page 2: '))

    def test_search_results_page_previous_link_is_present(self):
        d = self.get('/search/?q=monocot&page=2')
        self.assertTrue(d.find_element_by_link_text('Previous'))

    def test_search_results_page_next_link_is_present(self):
        d = self.get('/search/?q=monocot&page=2')
        self.assertTrue(d.find_element_by_link_text('Next'))

    def test_search_results_page_heading_number_has_thousands_comma(self):
        self.get('/search/?q=monocot')  # query that returns > 1,000 results
        heading = self.css('h1')
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
            # like '...Genus: Rhexia' rather than '...Rhexia'. This
            # means that our custom highlighter is adding some context
            # before the highlighted word as expected.
            if excerpt.text.startswith('...'):
                self.assertTrue(excerpt.text.find('...Rhexia') == -1)

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
            ('Quercus bicolor', 'swamp white oak'),
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

    def test_search_results_page_genus_returns_first_result(self):
        genera = ['Claytonia (spring-beauty)',
                  'Echinochloa (barnyard grass)',
                  'Koeleria (Koeler\'s grass)',
                  'Panicum (panicgrass)',
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
            self.assertEqual('Glossary: %s: %s' % (term[0].upper(), term),
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

    # Search on the word key

    def test_search_results_has_simple_key_main_page(self):
        self.get('/search/?q=key')
        result_links = self._result_links()
        self.assertTrue(len(result_links))
        self.assertTrue(self._is_page_found(result_links,
            'Simple Key for Plant Identification'))

    # TODO: enable when Full Key is added to the search feature
    #def test_search_results_has_full_key_main_page(self):
    #    self.get('/search/?q=key')
    #    result_links = self._result_links()
    #    self.assertTrue(len(result_links))
    #    self.assertTrue(self._is_page_found(result_links,
    #        'Full Key for Plant Identification'))

    def test_search_results_has_dichotomous_key_main_page(self):
        self.get('/search/?q=key')
        result_links = self._result_links()
        self.assertTrue(len(result_links))
        self.assertTrue(self._is_page_found(result_links,
            'Dichotomous Key to Families'))

    # Search on site feature name "Simple Key"

    def test_search_results_have_simple_key_pages(self):
        self.get('/search/?q=simple%20key')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 2)
        results_with_simple_key_in_title = []
        for link in result_links:
            if link.text.find('Simple Key') > -1:
                results_with_simple_key_in_title.append(link)
        # There should be at least two pages with Simple Key in the
        # title: any of the initial groups list page, the subgroups list
        # pages, and the subgroup results pages.
        self.assertTrue(len(results_with_simple_key_in_title) > 1)


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

    # Search on lookalike name

    def test_lookalikes_are_in_search_indexes_for_many_pages(self):
        self.get('/search/?q=sometimes+confused+with')
        page_links = self.css('.search-navigation li')
        self.assertTrue(len(page_links) > 10)   # more than 100 results

    #####
    # Dichotomous Key search results tests
    #####

    def test_search_results_contain_dichotomous_key_main_page(self):
        self.get('/search/?q=dichotomous%20key')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(
            result_links, 'Dichotomous Key to Families'))

    def test_search_results_contain_dichotomous_key_group_pages(self):
        self.get('/search/?q=group%201')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links,
                                            'Group 1: Dichotomous Key'))

    def test_search_results_contain_dichotomous_key_family_pages(self):
        self.get('/search/?q=cornaceae')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(
            result_links, 'Cornaceae: Dichotomous Key'))

    def test_search_results_contain_dichotomous_key_genus_pages(self):
        self.get('/search/?q=pseudolycopodiella')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(
            result_links, 'Pseudolycopodiella: Dichotomous Key'))

    def test_search_results_contain_dichotomous_key_breadcrumbs(self):
        self.get('/search/?q=liliaceae%20dichotomous')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertEqual(result_links[0].text, 'Liliaceae: Dichotomous Key')
        result_excerpts = self.css('#search-results-list li p')
        self.assertTrue(result_excerpts[0].text.find(
            'You are here: Dichotomous Key > Liliaceae') > -1);

    def test_search_results_contain_dichotomous_key_page_text(self):
        self.get('/search/?q=cystopteris%20difficult%20stunted')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertEqual(result_links[0].text, 'Cystopteris: Dichotomous Key')
        result_excerpts = self.css('#search-results-list li p')
        self.assertTrue(result_excerpts[0].text.find(
            'Cystopteris is a difficult genus due to hybridization') > -1);

    def test_search_results_contain_dichotomous_key_leads_text(self):
        self.get('/search/?q=rachises%20costae%20indusia')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertEqual(result_links[0].text, 'Cystopteris: Dichotomous Key')
        result_excerpts = self.css('#search-results-list li p')
        self.assertTrue(result_excerpts[0].text.find(
            '1b. Rachises, costae, and') > -1);

    def test_search_results_contain_dichotomous_key_single_lead_text(self):
        self.get('/search/?q=genus%20exactly%20one%20species')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        result_excerpts = self.css('#search-results-list li p')
        self.assertTrue(result_excerpts[0].text.find(
            'This genus contains exactly one species.') > -1);

    def test_search_results_contain_species_page_info_from_flora(self):
        self.get('/search/?q=understories%20cool%20woods')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        result_excerpts = self.css('#search-results-list li p')
        self.assertTrue(result_excerpts[0].text.find(
            '...the understories of cool woods.') > -1);

    # Test searching miscellaneous pages around the site (about, etc.)

    def test_search_results_contain_about_page(self):
        self.get('/search/?q=national%20science%20foundation')
        result_links = self._result_links()
        self.assertTrue(len(result_links))
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

    def test_search_results_contain_dichotomous_key_help_page(self):
        self.get('/search/?q=dichotomous%20key%20help')
        result_links = self._result_links()
        self.assertTrue(len(result_links) > 0)
        self.assertTrue(self._is_page_found(result_links,
            "What's a Dichotomous Key?"))

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

    # Search on terms containing various special characters.

    def test_search_results_found_hyphenated_words(self):
        self.get('/search/?q=meadow-rue')
        self.assertTrue(len(self._result_links()) > 0)

    def test_search_results_found_hyphenated_words_first_possessive(self):
        self.get('/search/?q=wild+goat%27s-rue')
        self.assertTrue(len(self._result_links()) > 0)


class HaystackHighlighterTestCase(unittest.TestCase):

    # Here are a few tests to document and build upon the behavior of
    # the highlighter that comes with Haystack.

    def setUp(self):
        self.new_highlighter = Highlighter

    def test_initialize(self):
        query = 'highlight'
        highlighter = self.new_highlighter(query)
        self.assertNotEqual(None, highlighter)

    def test_simple_highlight(self):
        text = 'This is some text with a word to highlight.'
        query = 'highlight'
        expected = '...<span class="highlighted">highlight</span>.'
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_with_excerpting(self):
        query = 'highlight'
        highlighter = self.new_highlighter(query)
        text = 'Please highlight and excerpt this text.'
        expected = ('...<span class="highlighted">highlight</span> '
                    'and excerpt this text.')
        self.assertEqual(expected, highlighter.highlight(text))
        text = ('Try highlighting highlight once and then highlight '
                'highlight again.')
        expected = ('...<span class="highlighted">highlight</span>ing '
                    '<span class="highlighted">highlight</span> once and '
                    'then <span class="highlighted">highlight</span> '
                    '<span class="highlighted">highlight</span> again.')
        self.assertEqual(expected, highlighter.highlight(text))
        text = ('This is a test of highlighting a very long string. This '
                'is a test of highlighting a very long string. This is a '
                'test of highlighting a very long string. This is a test '
                'of highlighting a very long string.')
        expected = ('...<span class="highlighted">highlight</span>ing a very'
                    ' long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string.')
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_ignore_no_text(self):
        query = 'highlight'
        highlighter = self.new_highlighter(query)
        text = ('Please highlight and excerpt this text. '
                '\n--\nThis is text that could be ignored.\n--\n '
                'Here is some more text to highlight.')
        expected = ('...<span class="highlighted">highlight</span> and '
                    'excerpt this text. \n--\nThis is text that could be '
                    'ignored.\n--\n Here is some more text to '
                    '<span class="highlighted">highlight</span>.')
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_multiple_words(self):
        text = 'This is some text with words to highlight.'
        query = 'words to highlight'
        expected = ('...<span class="highlighted">words</span> '
                    '<span class="highlighted">to</span> '
                    '<span class="highlighted">highlight</span>.')
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_word_possessive(self):
        text = 'This is some text about Chamaelirium, or devil\'s bit.'
        query = 'devil\'s'
        expected = ('...<span class="highlighted">devil\'s</span> bit.')
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_word_possessive_html_entity(self):
        text = 'This is some text about Chamaelirium, or devil&#39;s bit.'
        query = 'devil&#39;s'
        expected = ('...<span class="highlighted">devil&#39;s</span> bit.')
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))


class ExtendedHighlighterTestCase(HaystackHighlighterTestCase):

    def setUp(self):
        self.new_highlighter = ExtendedHighlighter
        self.base = super(ExtendedHighlighterTestCase, self)

    # Override and add tests here as needed.
    #
    # If you expect a test to have *the same* result for the
    # ExtendedHighlighter as for the regular one, there is nothing to
    # add for it. All tests in the base class will run for the
    # ExtendedHighlighter too.
    #
    # On the other hand, if you expect a test to have *different*
    # result for the ExtendedHighlighter than for the regular one, just
    # override the test with new code.

    def test_simple_highlight(self):
        # One word to the left of the excerpt is shown.
        text = 'This is some text with a word to highlight.'
        query = 'highlight'
        expected = '...to <span class="highlighted">highlight</span>.'
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_with_excerpting(self):
        # One word to the left of the excerpt is shown.
        query = 'highlight'
        highlighter = self.new_highlighter(query)
        text = 'Please highlight and excerpt this text.'
        expected = ('Please <span class="highlighted">highlight</span> '
                    'and excerpt this text.')
        self.assertEqual(expected, highlighter.highlight(text))
        text = ('Please try highlighting highlight once and then highlight '
                'highlight again.')
        expected = ('...try <span class="highlighted">highlight</span>ing '
                    '<span class="highlighted">highlight</span> once and '
                    'then <span class="highlighted">highlight</span> '
                    '<span class="highlighted">highlight</span> again.')
        self.assertEqual(expected, highlighter.highlight(text))
        text = ('This is a test of highlighting a very long string. This '
                'is a test of highlighting a very long string. This is a '
                'test of highlighting a very long string. This is a test '
                'of highlighting a very long string.')
        expected = ('...of <span class="highlighted">highlight</span>ing a '
                    'very long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string.')
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_ignore_no_text(self):
        # One word to the left of the excerpt is shown.
        query = 'highlight'
        highlighter = self.new_highlighter(query)
        text = ('Please highlight and excerpt this text. '
                '\n--\nThis is text that could be ignored.\n--\n '
                'Here is some more text to highlight.')
        expected = ('Please <span class="highlighted">highlight</span> and '
                    'excerpt this text. \n--\nThis is text that could be '
                    'ignored.\n--\n Here is some more text to '
                    '<span class="highlighted">highlight</span>.')
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_multiple_words(self):
        text = 'This is some text with words to highlight.'
        query = 'words to highlight'
        expected = ('...with <span class="highlighted">words</span> '
                    '<span class="highlighted">to</span> '
                    '<span class="highlighted">highlight</span>.')
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_word_possessive(self):
        text = 'This is some text about Chamaelirium, or devil\'s bit.'
        query = 'devil\'s'
        expected = ('...or <span class="highlighted">devil\'s</span> bit.')
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_word_possessive_html_entity(self):
        text = 'This is some text about Chamaelirium, or devil&#39;s bit.'
        query = 'devil&#39;s'
        expected = ('...or <span class="highlighted">devil&#39;s</span> bit.')
        highlighter = self.new_highlighter(query)
        self.assertEqual(expected, highlighter.highlight(text))

    # Add new tests for options that the regular highlighter doesn't
    # have.

    def test_highlighter_set_excerpt_option(self):
        query = 'highlight'
        highlighter = self.new_highlighter(query, excerpt=False)
        self.assertEqual(False, highlighter.excerpt)
        highlighter = self.new_highlighter(query, excerpt=True)
        self.assertEqual(True, highlighter.excerpt)
        highlighter = self.new_highlighter(query)
        self.assertEqual(True, highlighter.excerpt)

    def test_highlight_without_excerpting(self):
        query = 'highlight'
        highlighter = self.new_highlighter(query, excerpt=False)
        text = 'Please highlight but do not excerpt this text.'
        expected = ('Please <span class="highlighted">highlight</span> '
                    'but do not excerpt this text.')
        self.assertEqual(expected, highlighter.highlight(text))
        text = ('Try highlighting highlight once and then highlight '
                'highlight again.')
        expected = ('Try <span class="highlighted">highlight</span>ing '
                    '<span class="highlighted">highlight</span> once and '
                    'then <span class="highlighted">highlight</span> '
                    '<span class="highlighted">highlight</span> again.')
        self.assertEqual(expected, highlighter.highlight(text))
        text = ('This is a test of highlighting a very long string. This '
                'is a test of highlighting a very long string. This is a '
                'test of highlighting a very long string. This is a test '
                'of highlighting a very long string.')
        expected = ('This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long string. This is a test of '
                    '<span class="highlighted">highlight</span>ing a very '
                    'long stri...')
        self.assertEqual(expected, highlighter.highlight(text))

    def test_highlight_ignore_text_between_markers(self):
        query = 'highlight'
        marker_regex = '\n--\n'
        highlighter = self.new_highlighter(query,
                                           ignore_between=marker_regex)
        text = ('Please now highlight and excerpt this text. '
                '\n--\nThis is text that should be ignored.\n--\n '
                'Here is some more text to highlight. '
                '\n\n--\n\n\nHere is some more to ignore.\n '
                'And yet more to ignore.\n\n\n--\n'
                'Here is a bit more to highlight.')
        expected = ('...now <span class="highlighted">highlight</span> and '
                    'excerpt this text.  Here is some more text to '
                    '<span class="highlighted">highlight</span>. '
                    '\nHere is a bit more to '
                    '<span class="highlighted">highlight</span>.')
        self.assertEqual(expected, highlighter.highlight(text))


if __name__ == '__main__':
    unittest.main()

"""Tests for the Simple Key application."""

import re
from gobotany.libtest import FunctionalCase
from selenium.common.exceptions import NoSuchElementException


class FamilyTests(FunctionalCase):

    def test_family_page(self):
        self.get('/family/lycopodiaceae/')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text == 'Family: Lycopodiaceae')
        common_name = self.css('#main h3')
        self.assertTrue(len(common_name))

    def test_family_page_has_example_images(self):
        self.get('/family/lycopodiaceae/')
        example_images = self.css('#main .pics a img')
        self.assertTrue(len(example_images))

    def test_family_page_has_list_of_genera(self):
        self.get('/family/lycopodiaceae/')
        genera = self.css('#main .genera li')
        self.assertTrue(len(genera))


class GenusTests(FunctionalCase):

    def test_genus_page(self):
        self.get('/genus/dendrolycopodium/')
        heading = self.css('#main h2')
        self.assertTrue(len(heading))
        self.assertTrue(heading[0].text == 'Genus: Dendrolycopodium')
        common_name = self.css('#main h3')
        self.assertTrue(len(common_name))
        self.assertTrue(common_name[0].text == 'tree-clubmoss')

    def test_genus_page_has_example_images(self):
        self.get('/genus/dendrolycopodium/')
        example_images = self.css('#main .pics a img')
        self.assertTrue(len(example_images))

    def test_genus_page_has_family_link(self):
        self.get('/genus/dendrolycopodium/')
        family_link = self.css('#main p.family a')
        self.assertTrue(len(family_link))

    def test_genus_page_has_list_of_species(self):
        self.get('/genus/dendrolycopodium/')
        species = self.css('#main .species li')
        self.assertTrue(len(species))


class SpeciesTests(FunctionalCase):

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
        species_page_url = '/species/dendrolycopodium/dendroideum/'
        self._photos_have_expected_caption_format(species_page_url)

    def test_species_page_photos_have_title_credit_copyright_source(self):
        # Some images on this page have "sources" specified for them.
        species_page_url = ('/species/gymnocarpium/dryopteris/')
        self._photos_have_expected_caption_format(species_page_url)

    def test_simple_key_species_page_has_breadcrumb(self):
        self.get('/species/adiantum/pedatum/')
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


class LookalikesFunctionalTests(FunctionalCase):

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

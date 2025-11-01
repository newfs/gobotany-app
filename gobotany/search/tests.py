import requests
import unittest

from django.conf import settings
from django.test.client import Client
from django.test.testcases import TestCase

from lxml import etree
from lxml.cssselect import CSSSelector

from haystack.utils import Highlighter

from .highlight import ExtendedHighlighter

# To run all search tests:
#
# dev/test-python search
#
# To run a single test:
#
# dev/test-python search.SearchTests.{test_function_name}

class SearchTests(TestCase):

    def css(self, response, selector):
        if response.status_code == 200:
            content = response.content
            if content.startswith(b'<?xml'):
                self.tree = etree.fromstring(content)
            else:
                parser = etree.HTMLParser()
                self.tree = etree.fromstring(content, parser)

        lxml_elements = CSSSelector(selector)(self.tree)
        return [ element for element in lxml_elements ]

    def test_search_results_page(self):
        # No results will be found because the test client doesn't connect to
        # Solr, but the query word will be in the page heading.
        response = self.client.get('/search/?q=acer')
        heading1 = self.css(response, 'h1')
        heading_text = str(etree.tostring(heading1[0]))
        self.assertTrue(heading_text.find('acer') > -1)


class HaystackHighlighterTestCase(TestCase):

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

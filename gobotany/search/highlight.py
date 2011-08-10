import re

from django.utils.html import strip_tags

from haystack.utils import Highlighter


class ExtendedHighlighter(Highlighter):
    excerpt = True   # Whether highlighted text can start with '...' excerpt
    ignore_between = None   # Ignore text between regular expression markers

    def __init__(self, query, **kwargs):
        if 'excerpt' in kwargs:
            self.excerpt = str(kwargs['excerpt']).lower() != 'false'
        if 'ignore_between' in kwargs:
            self.ignore_between = kwargs['ignore_between']

        super(ExtendedHighlighter, self).__init__(query, **kwargs)


    def _strip_text_to_ignore(self, text_block):
        ignore_regex = '%s.*?%s' % (self.ignore_between,
                                    self.ignore_between)
        compiled_regex = re.compile(ignore_regex, re.DOTALL)
        return re.sub(compiled_regex, '', text_block)


    def _previous_word_offset(self, text_block, start_offset):
        # Given text and a starting character offset, return a new
        # offset for one word to the left of the original offset.
        previous_word_offset = 0
        if start_offset > 1:
            # Find the end of the previous word.
            for i in reversed(xrange(0, start_offset)):
                if text_block[i] != ' ':
                    end_previous_word_offset = i
                    break
            # Find the beginning of the previous word.
            for i in reversed(xrange(0, end_previous_word_offset)):
                if text_block[i] == ' ':
                    previous_word_offset = i + 1
                    break

        return previous_word_offset


    def highlight(self, text_block):
        self.text_block = strip_tags(text_block)

        if self.ignore_between:
            self.text_block = self._strip_text_to_ignore(self.text_block)

        highlight_locations = self.find_highlightable_words()

        start_offset = 0
        end_offset = self.max_length
        if self.excerpt:
            start_offset, end_offset = self.find_window(highlight_locations)
            # Reveal one word to the left of where the excerpt starts
            # in order to show some more context.
            if start_offset > 0:
                start_offset = self._previous_word_offset(self.text_block,
                                                          start_offset)
                # Adjust the end offset if necessary so as to not to
                # exceed the maximum length.
                if (end_offset - start_offset) > self.max_length:
                    end_offset = start_offset + self.max_length

        return self.render_html(highlight_locations, start_offset,
                                end_offset)

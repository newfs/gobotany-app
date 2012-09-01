import re
from django import template
from django.utils.safestring import mark_safe

from haystack.templatetags.highlight import HighlightNode

from gobotany.search.highlight import ExtendedHighlighter

register = template.Library()


class ExtendedHighlightNode(HighlightNode):
    def __init__(self, text_block, query, var_name, html_tag=None,
                 css_class=None, max_length=None, excerpt=None,
                 ignore_between=None):
        self.excerpt = excerpt
        self.ignore_between = None
        self.var_name = var_name

        if excerpt is not None:
            self.excerpt = template.Variable(excerpt)

        if ignore_between is not None:
            self.ignore_between = template.Variable(ignore_between)

        super(ExtendedHighlightNode, self).__init__(text_block, query,
            html_tag=html_tag, css_class=css_class, max_length=max_length)


    def render(self, context):
        text_block = self.text_block.resolve(context)
        query = self.query.resolve(context)
        kwargs = {}

        if self.html_tag is not None:
            kwargs['html_tag'] = self.html_tag.resolve(context)

        if self.css_class is not None:
            kwargs['css_class'] = self.css_class.resolve(context)

        if self.max_length is not None:
            kwargs['max_length'] = self.max_length.resolve(context)

        if self.excerpt is not None:
            kwargs['excerpt'] = self.excerpt.resolve(context)

        if self.ignore_between is not None:
            kwargs['ignore_between'] = self.ignore_between.resolve(context)

        # Remove quotation marks from inside the query, since the text
        # we are highlighting will lack them; otherwise, a query like
        # 'q="acer"' will get no highlighting in its results.  This is
        # also necessary if quoted phrases, such as 'q="blue flower"',
        # are to receive useful search summaries.

        query = query.replace('"', ' ')

        # The parent class allows for a custom highlighter class to be
        # pulled in. Here instead, just the ExtendedHighlighter class
        # that goes with this template tag code is used, so as to leave
        # alone the default Haystack custom highlighter class setting,
        # and because the ability to override the highlighter class is
        # not yet needed here.

        highlighter = ExtendedHighlighter(query, **kwargs)
        highlighted_text = highlighter.highlight(text_block)
        context[self.var_name] = mark_safe(highlighted_text)
        return ''


@register.tag
def search_highlight(parser, token):
    """Takes a block of text and highlights words from a provided query
    within that block of text. Optionally accepts arguments to provide
    the HTML tag to wrap highlighted word in, a CSS class to use with
    the tag, a maximum length of the blurb in characters, and whether
    to excerpt the text at the beginning of the output.

    Syntax::

        {% highlight <text_block> with <query> as <var_name>
        [css_class "class_name"] [html_tag "span"] [max_length 200]
        [excerpt 'False'] [ignore_between '\n--\n'] %}

    Examples::

        # Highlight summary with default behavior.
        {% highlight result.summary with request.query as my_summary %}

        # Highlight summary but wrap highlighted words with a div and the
        # following CSS class.
        {% highlight result.summary with request.query as my_summary
        html_tag "div" css_class "highlight_me_please" %}

        # Highlight summary but only show 40 characters.
        {% highlight result.summary with request.query as my_summary
        max_length 40 %}

        # Highlight summary but do not excerpt text at the beginning.
        {% highlight result.summary with request.query as my_summary
        excerpt 'False' %}

        # Highlight summary but ignore any text between markers that
        # match the given regular expression.
        # Markers are the same at the beginning and end of the piece to
        # be ignored: there are no opening and closing styles.
        {% highlight result.summary with request.query as my_summary
        ignore_between '\n--\n' %}
    """
    bits = token.split_contents()
    tag_name = bits[0]

    if not len(bits) % 2 == 0:
        raise template.TemplateSyntaxError(u"'%s' tag requires valid "
            "pairings arguments." % tag_name)

    text_block = bits[1]

    if len(bits) < 4:
        raise template.TemplateSyntaxError(u"'%s' tag requires an object "
            "and a query provided by 'with'." % tag_name)

    if bits[2] != 'with':
        raise template.TemplateSyntaxError(u"'%s' tag's second argument "
            "should be 'with'." % tag_name)

    query = bits[3]
    # bits[4] = 'as'
    var_name = bits[5]

    arg_bits = iter(bits[6:])
    kwargs = {}

    for bit in arg_bits:
        if bit == 'css_class':
            kwargs['css_class'] = arg_bits.next()

        if bit == 'html_tag':
            kwargs['html_tag'] = arg_bits.next()

        if bit == 'max_length':
            kwargs['max_length'] = arg_bits.next()

        if bit == 'excerpt':
            kwargs['excerpt'] = arg_bits.next()

        if bit == 'ignore_between':
            kwargs['ignore_between'] = arg_bits.next()

    return ExtendedHighlightNode(text_block, query, var_name, **kwargs)


element_re = re.compile('(<[^>]*>)')

@register.filter
def quick_highlight(text, query):
    """Quick highlighter, for situations where complexity causes trouble.

    The `text` is expected to be HTML, and we are careful not to attempt
    any highlighting withing elements.

    """
    def embolden(match):
        return u'<b>{}</b>'.format(match.group(0))

    # Without a query, there are no words to highlight.

    words = query.split()
    if not words:
        return text

    # Otherwise, we prepare to highlight any query word that we happen
    # to find within the text.

    escaped_words = (re.escape(word) for word in words)
    word_match = u'|'.join(ur'\b{}\b'.format(word) for word in escaped_words)
    words_re = re.compile(word_match, flags=re.I)

    # We step across the even-numbered elements in our list, to only
    # highlight within non-element stretches of text.

    words_and_elements = element_re.split(text)

    for i in range(0, len(words_and_elements), 2):
        subtext = words_and_elements[i]
        words_and_elements[i] = words_re.sub(embolden, subtext)

    return ''.join(words_and_elements)

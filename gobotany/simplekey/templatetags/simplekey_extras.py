import re

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

# "Collect" tag courtesy of http://djangosnippets.org/snippets/2196/
# Collects items into a list that can be used later in the template.
@register.tag
def collect(parser, token):
    bits = list(token.split_contents())
    if len(bits) > 3 and bits[-2] == 'as':
        varname = bits[-1]
        items = bits[1:-2]
        return CollectNode(items, varname)
    else:
        raise template.TemplateSyntaxError( \
            '%r expected format is "item [item ...] as varname"' % bits[0])

class CollectNode(template.Node):
    def __init__(self, items, varname):
        self.items = map(template.Variable, items)
        self.varname = varname

    def render(self, context):
        context[self.varname] = [i.resolve(context) for i in self.items]
        return ''


@register.filter
@stringfilter
def replace(value, arg):
    '''Replace the first supplied character with the second.'''
    characters = arg.split(',')
    return value.replace(characters[0], characters[1])


def _italicize_word(word):
    """Italicize a word in HTML, unless already done."""
    if word.find('<i>') == -1:
        return '<i>' + word + '</i>'
    else:
        return word

@register.filter
@stringfilter
def italicize_plant(value):
    """Italicize the latin parts of a plant scientific name.
    Try to handle a bit of surrounding text to allow this filter to
    be used in other situations, such as the 'Notes on Subspecies
    and Varieties' on the species page.
    """

    # Support for sentences is limited to the ones from 'Notes on
    # Subspecies and Varieties.' These end with a New England state
    # abbreviation followed by a period.
    sentence_regex = re.compile(r'(.*(?:CT|MA|ME|NH|RI|VT|and is rare)\.)')
    sentences = sentence_regex.split(value)
    sentences = [sentence.strip() for sentence in sentences
                 if len(sentence.strip()) > 0]

    new_sentences = []
    for sentence in sentences:
        words = sentence.split(' ')

        # Join any false word breaks resulting from HTML span tags added
        # for search result highlighting.
        fixed_words = []
        for count, word in enumerate(words):
            # If the word contains an opening HTML span tag, join it with
            # the next word, which will contain the closing HTML span tag.
            # (A pair of highlight span tags only surrounds a single word.)
            if word.find('<span') > -1:
                try:
                    new_word = word + ' ' + words[count + 1]
                except IndexError:
                    pass
            elif word.find('</span>') > -1:
                # If it contains a closing HTML span tag, ignore it because
                # it has already been joined with the opening tag.
                continue
            else:
                new_word = word
            fixed_words.append(new_word)
        words = fixed_words

        if len(words) >= 2:
            # Usually the first two words are the genus and specific
            # epithet, but there are a few special cases to handle.
            remaining_start = 2
            if words[0] == 'Genus':
                words[1] = _italicize_word(words[1])
            elif ' '.join(words[0:3]) in ['Our subspecies is',
                                          'Our variety is']:
                words[3] = _italicize_word(words[3])
                words[4] = _italicize_word(words[4])
                remaining_start = 5
            elif ' '.join(words[0:5]) == 'Our subspecies and variety is':
                words[6] = _italicize_word(words[6])
                words[7] = _italicize_word(words[7])
                remaining_start = 8
            else:
                words[0] = _italicize_word(words[0])
                words[1] = _italicize_word(words[1])

            # Look for more words to italicize, such as epithets in a variety
            # or subspecies name.
            CONNECTING_TERMS = ['subsp.', 'ssp.', 'var.', 'subvar.', 'f.',
                                'forma', 'subf.']
            for i in range(remaining_start, len(words)):
                try:
                    if words[i] in CONNECTING_TERMS:
                        # Check also for whether the next word is a
                        # connecting term, such as with "L. f. var.".
                        if words[i + 1] not in CONNECTING_TERMS:
                            words[i + 1] = _italicize_word(words[i + 1])
                except IndexError:
                    pass
        new_sentences.append(' '.join(words))

    return ' '.join(new_sentences)


@register.filter
@stringfilter
def italicize_infraspecific_names(value):
    """Italicize any infraspecific names found in the text."""
    pattern = re.compile(r'(subsp.|ssp.|var.|subvar.|f.|subf.)\s(\w+)')
    italicized_value = re.sub(pattern, r'\1 <i>\2</i>', value)
    return italicized_value


@register.filter
def habitat_names(character_values):
    """For each habitat character-value, create a pretty name.

    This routine takes a list of `CharacterValue` objects representing
    habitats, and returns a list of strings like:

        u'Lacustrine (in lakes or ponds)'

    But it refuses to return strings like:

        u'Forests (forests)'

    See the unit test for this routine, which is actually an exhaustive
    test: it pits this function against every actual habitat value that
    we currently have, so that the test-writer can eyeball the results
    and make sure they all read well.

    """
    def words_inside(text):
        return set(word.rstrip(u's') for word in text.split()
                   if word not in (u'and', u'of', u'or'))

    names = []
    for cv in character_values:
        s = cv.value_str.lower()
        t = cv.friendly_text.lower()

        if '/' in s:
            # Any value_str that contains a slash is trying to squeeze
            # in so much information that we should just stick with the
            # friendly_text.
            name = t
        elif '(' in t:
            # If the friendly_text already has a parenthesis, then it
            # is already complex enough to stand alone.
            name = t
        elif words_inside(s) >= words_inside(t):
            # If the friendly_text adds no interesting words to the
            # description, then choose the value_str since it will
            # probably be pithier.
            name = s
        elif t.startswith(s):
            # If the friendly_text starts with the value_str, then we
            # need not repeat ourselves by showing both.
            name = t
        else:
            name = u'{} ({})'.format(s, t)
        names.append(name)
    return names


@register.filter
@stringfilter
def repeat(value, arg):
    """Repeat a phrase N times.

    The template expression::

        {{ species.name|repeat:4 }}

    becomes::

        Acer rubrum Acer rubrum Acer rubrum Acer rubrum

    """
    return ' '.join([ value ] * arg)


# Inclusion tag for formatting a combined title/credit/copyright string
# for use with a photo.
@register.inclusion_tag('gobotany/_photo_credit.html')
def photo_credit(image, image_name):
    return {'image': image, 'image_name': image_name}

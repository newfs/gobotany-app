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


@stringfilter
def split(value, arg):
    '''Split a string into a list on the given character.'''
    return value.split(arg)


def at_index(value, arg):
    '''Return the list item at the specified index.'''
    return value[int(arg)]


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
    sentence_regex = re.compile(r'(.*(?:CT|MA|ME|NH|RI|VT)\.)')
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


# Range filter courtesy of http://djangosnippets.org/snippets/1357/
# Allows a for loop to a number defined in the template.
def get_range(value):
  """
    Filter - returns a list containing range made from given value
    Usage (in template):

    <ul>{% for i in 3|get_range %}
      <li>{{ i }}. Do something</li>
    {% endfor %}</ul>

    Results with the HTML:
    <ul>
      <li>0. Do something</li>
      <li>1. Do something</li>
      <li>2. Do something</li>
    </ul>

    Instead of 3 one may use the variable set in the views
  """
  return range(value)


# Inclusion tag for formatting a combined title/credit/copyright string
# for use with a photo.
def photo_credit(image, image_name):
    return {'image': image, 'image_name': image_name}

register.filter('split', split)
register.filter('at_index', at_index)
register.filter('replace', replace)
register.filter('italicize_plant', italicize_plant)
register.filter('get_range', get_range)

register.inclusion_tag( \
    'simplekey/_photo_credit.html')(photo_credit)

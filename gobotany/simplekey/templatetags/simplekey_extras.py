from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

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
    return '<i>' + word + '</i>'

@stringfilter
def italicize_plant(value):
    '''Italicize the latin parts of a plant scientific name.'''
    words = value.split(' ')
    # Assume the first two words are the genus and specific epithet.
    words[0] = _italicize_word(words[0])
    words[1] = _italicize_word(words[1])
    # Look for more words to italicize, such as a variety or subspecies.
    CONNECTING_TERMS = ['subsp.', 'ssp.', 'var.', 'subvar.', 'f.',
                        'forma', 'subf.']
    for i in range(2 , len(words)):
        if words[i] in CONNECTING_TERMS and words[i + 1]:
            words[i + 1] = _italicize_word(words[i + 1])
    return ' '.join(words)


register.filter('split', split)
register.filter('at_index', at_index)
register.filter('replace', replace)
register.filter('italicize_plant', italicize_plant)

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


register.filter('split', split)
register.filter('at_index', at_index)
register.filter('replace', replace)


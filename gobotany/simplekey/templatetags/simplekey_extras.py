from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@stringfilter
def split(value, arg):
    '''Splits a string into a list on the given character.'''
    return value.split(arg)


def index(value, arg):
    '''Return the list item at the specified index.'''
    return value[int(arg)]


register.filter('split', split)
register.filter('index', index)

# -*- coding: utf-8 -*-

"""Compute the display title of a Couplet."""

import re
from django import template

register = template.Library()

def abbr(s):
    """Abbreviate 'Huperzia appressa' to 'H. appressa'."""
    parts = s.split(None, 1)
    if len(parts) < 2:
        return s
    genus, rest = s.split(None, 1)
    return u'%s. %s' % (genus[0], rest)

def cslug(couplet):
    if not couplet:
        return 'Family-Carex'
    return couplet.title.replace(u' ', u'-')

def ctitle(couplet):
    if couplet.rank == 'family':
        return u'Family {}'.format(couplet.title)
    elif couplet.rank == 'genus' or couplet.rank == 'species':
        return u'<i>{}</i>'.format(couplet.title)
    elif couplet.title:
        return couplet.title
    else:
        return unicode(couplet.number)

re_floating_figure = re.compile(ur'<FIG-(\d+)>')  # see parser.py
re_figure_mention = re.compile(ur'\[Fig(s?)\. ([\d, ]+)\]')

def render_floating_figure(match):
    number = match.group(1)
    return (
        u'<span class="figure">'
        u'<a class="figure-link" href="/figures/figure-%s.png">'
        u'<img src="/figures/figure-%s.png">'
        u'</a>'
        u'<span class="number">Fig. %s.</span>'
        u'%s'
        u'</span>'
        ) % (number, number, number, 'TODO: PUT CAPTION HERE')
# caption used to be grabbed from: info.captions[int(number)])

def render_figure_mention(match):
    ess = match.group(1)
    numbers = [ number.strip() for number in match.group(2).split(',') ]
    return (
        u'[Fig%s. '
        + u', '.join([
                u'<a class="figure-link" href="/figures/figure-%s.png">'
                u'%s'
                u'</a>'
                % (number, number) for number in numbers
                ])
        + u']'
        ) % (ess,) #number, number, number, captions[int(number)])

def figurize(text):
    text = re_floating_figure.sub(render_floating_figure, text)
    text = re_figure_mention.sub(render_figure_mention, text)
    return text

def lastword(text):
    return text.split()[-1]

def length(thing):
    return len(thing)

def replace(text, arg):
    a, b = arg.split(':', 1)
    return text.replace(a, b)

def strip(text, chars=None):
    return text.strip(chars)

register.filter('abbr', abbr)
register.filter('cslug', cslug)
register.filter('ctitle', ctitle)
register.filter('figurize', figurize)
register.filter('lastword', lastword)
register.filter('length', length)
register.filter('replace', replace)
register.filter('strip', strip)

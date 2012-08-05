# -*- coding: utf-8 -*-

"""Compute the display title of a Couplet."""

import re
from django import template
from django.utils.safestring import SafeUnicode, mark_safe
from gobotany.dkey import models

register = template.Library()

def abbr(s):
    """Abbreviate 'Huperzia appressa' to 'H. appressa'."""
    parts = s.split(None, 1)
    if len(parts) < 2:
        return s
    genus, rest = s.split(None, 1)
    return u'%s. %s' % (genus[0], rest)

def breadcrumbs(page):
    if not page.breadcrumb_ids:
        return []
    ids = [ int(n) for n in page.breadcrumb_ids.split(',') ]
    pages = models.Page.objects.filter(id__in=ids)
    return sorted(pages, key=lambda page: len(page.breadcrumb_ids))

def cslug(couplet):
    if not couplet:
        return 'Family-Carex'
    return couplet.title.replace(u' ', u'-')

def display_title(page):
    if page.rank == 'family':
        return u'Family {}'.format(page.title)
    elif page.rank == 'genus' or page.rank == 'species':
        return mark_safe(u'<i>{}</i>'.format(page.title))
    else:
        return page.title

re_floating_figure = re.compile(ur'<FIG-(\d+)>')  # see parser.py
re_figure_mention = re.compile(ur'\[Fig(s?)\. ([\d, ]+)\]')

def render_floating_figure(match):
    number = int(match.group(1))
    figure = models.Figure.objects.get(number=number)
    return (
        u'<span class="figure">'
        u'<a class="figure-link" href="/figures/figure-%s.png">'
        u'<img src="/figures/figure-%s.png">'
        u'</a>'
        u'<span class="number">Fig. %s.</span>'
        u'%s'
        u'</span>'
        ) % (number, number, number, figure.caption)
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

def nobr(text):
    new = text.replace(u' ', u'\u00a0')
    return mark_safe(new) if isinstance(text, SafeUnicode) else new

def replace(text, arg):
    a, b = arg.split(':', 1)
    return text.replace(a, b)

def slug(page, chars=None):
    return page.title.replace(u' ', u'-')

def strip(text, chars=None):
    return text.strip(chars)

register.filter('abbr', abbr)
register.filter('breadcrumbs', breadcrumbs)
register.filter('cslug', cslug)
register.filter('display_title', display_title)
register.filter('figurize', figurize)
register.filter('lastword', lastword)
register.filter('nobr', nobr)
register.filter('replace', replace)
register.filter('slug', slug)
register.filter('strip', strip)

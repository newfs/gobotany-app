# -*- coding: utf-8 -*-

"""Compute the display title of a Couplet."""

import re
from django.template import Context, Library
from django.template.loader import get_template
from django.utils.safestring import SafeUnicode, mark_safe
from gobotany.dkey import models

register = Library()

plurals = {
    'family': 'families',
    'genus': 'genera',
    'species': 'species',
    'tribe': 'tribes',
    }

def abbreviate_title(s):
    """Make 'Acer rubrum' 'A. rubrum' and remove 'Group' from group titles."""
    if u'Group ' in s:
        return s.replace(u'Group ', u'')
    else:
        parts = s.split(None, 1)
        if len(parts) < 2:
            return s
        genus, rest = s.split(None, 1)
        return u'%s. %s' % (genus[0], rest)

def breadcrumbs(page):
    return page.breadcrumb_cache.order_by('id')

def display_title(page):
    if page.rank == 'family':
        return u'Family {}'.format(page.title)
    elif page.rank == 'genus' or page.rank == 'species':
        return mark_safe(u'<i>{}</i>'.format(page.title))
    else:
        return page.title

def figure_url(figure):
    return 'http://newfs.s3.amazonaws.com/dkey-figures/figure-{}.png'.format(
        figure.number)

def genus_slug(page_title):
    return page_title.split()[0].lower()

re_floating_figure = re.compile(ur'<FIG-(\d+)>')  # see parser.py
re_figure_mention = re.compile(ur'\[Figs?\. ([\d, ]+)\]')

def render_floating_figure(match):
    number = int(match.group(1))
    figure = models.Figure.objects.get(number=number)
    return get_template('dkey/figure.html').render(Context({'figure': figure}))

def render_figure_mention(match):
    numbers = [ int(number) for number in match.group(1).split(',') ]
    figures = list(models.Figure.objects.filter(number__in=numbers))
    context = Context({'figures': figures})
    return get_template('dkey/figure_mention.html').render(context)

def figurize(text):
    text = re_floating_figure.sub(render_floating_figure, text)
    text = re_figure_mention.sub(render_figure_mention, text)
    return text

def lastword(text):
    return text.split()[-1]

def nobr(text):
    new = text.replace(u' ', u'\u00a0')
    return mark_safe(new) if isinstance(text, SafeUnicode) else new

def slug(page, chars=None):
    return page.title.replace(u' ', u'-')

def species_slug(page_title):
    return page_title.split()[1].lower()

def taxon_plural(s):
    return plurals[s]

register.filter('abbreviate_title', abbreviate_title)
register.filter('breadcrumbs', breadcrumbs)
register.filter('display_title', display_title)
register.filter('figure_url', figure_url)
register.filter('figurize', figurize)
register.filter('genus_slug', genus_slug)
register.filter('lastword', lastword)
register.filter('nobr', nobr)
register.filter('slug', slug)
register.filter('species_slug', species_slug)
register.filter('taxon_plural', taxon_plural)

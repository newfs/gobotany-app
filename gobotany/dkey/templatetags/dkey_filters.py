# -*- coding: utf-8 -*-

"""Compute the display title of a Couplet."""

import json as json_module
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

short_group_texts = {

    # These are briefer than the equivalent texts in gobotany.dkey.views
    # so that the breadcrumb navigation does not become overly verbose.

    1: u'Lycophytes, Monilophytes',
    2: u'Gymnosperms',
    3: u'Monocots',
    4: u'Woody angiosperms with opposite or whorled leaves',
    5: u'Woody angiosperms with alternate leaves',
    6: u'Herbaceous angiosperms with inferior ovaries',
    7: u'Herbaceous angiosperms with superior ovaries and zygomorphic flowers',
    8: u'Herbaceous angiosperms with superior ovaries, actinomorphic flowers, '
       u'and 2 or more distinct carpels',
    9: u'Herbaceous angiosperms with superior ovaries, actinomorphic flowers, '
       u'connate petals, and a solitary carpel or 2 or more connate carpels',
    10:u'Herbaceous angiosperms with superior ovaries, actinomorphic flowers, '
       u'distinct petals or the petals lacking, and 2 or more connate carpels',
    }

@register.filter
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

@register.filter
def breadcrumbs(page):
    return page.breadcrumb_cache.order_by('id')

@register.filter
def display_title(page):
    if page.rank == 'family':
        return u'Family {}'.format(page.title)
    elif page.rank == 'genus' or page.rank == 'species':
        return mark_safe(u'<i>{}</i>'.format(page.title))
    else:
        return page.title

@register.filter
def dkey_url(name):
    name = name.lower()
    if ' ' in name and not name.startswith('group '):
        return '/species/' + name.replace(' ', '/') + '/?key=dichotomous';
    else:
        return '/dkey/' + name.replace(' ', '-') + '/';

@register.filter
def expand_group_title(title):
    if not title.startswith('Group '):
        return title
    number = int(title[6:])
    return u'{}: {}'.format(title, short_group_texts[number])

@register.filter
def figure_url(figure):
    return 'http://newfs.s3.amazonaws.com/dkey-figures/figure-{}.png'.format(
        figure.number)

@register.filter
def genus_slug(page_title):
    return page_title.split()[0].lower()

re_floating_figure = re.compile(ur'<FIG-(\d+)>')  # see parser.py

# The [RL] is because Figure 834 has two pieces, Right and Left,
# designated with references like "[Fig. 834, L]". The "\s*" catches
# some malformed figure references like "[Fig. 940 \n]".
re_figure_link = re.compile(ur'\[Figs?\. ([\d, ]+)(, [RL])?\s*\]')

@register.filter
def render_floating_figure(match):
    number = int(match.group(1))
    figure = models.Figure.objects.get(number=number)
    return get_template('dkey/figure.html').render(Context({'figure': figure}))

@register.filter
def render_figure_link(match):
    numbers = [ int(number) for number in match.group(1).split(',') ]
    figures = list(models.Figure.objects.filter(number__in=numbers))
    context = Context({'figures': figures, 'suffix': match.group(2) or ''})
    return get_template('dkey/figure_link.html').render(context)

@register.filter
def render_floating_figures(text):
    text = re_floating_figure.sub(render_floating_figure, text)
    return text

@register.filter
def discard_floating_figures(text):
    text = re_floating_figure.sub('', text)
    return text

@register.filter
def render_figure_links(text):
    text = re_figure_link.sub(render_figure_link, text)
    return text

@register.filter
def json(anything):
    if isinstance(anything, set):
        anything = list(anything)
    return json_module.dumps(anything)

@register.filter
def lastword(text):
    return text.split()[-1]

@register.filter
def nobr(text):
    new = text.replace(u' ', u'\u00a0')
    return mark_safe(new) if isinstance(text, SafeUnicode) else new

@register.filter
def slug(page, chars=None):
    return page.title.lower().replace(u' ', u'-')

@register.filter
def species_slug(page_title):
    return page_title.split()[1].lower()

@register.filter
def taxon_plural(s):
    return plurals[s]

from itertools import groupby
from operator import attrgetter

from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.dkey import models

group_texts = {
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

group_texts_sorted = sorted(key_value for key_value in group_texts.items())

def fill_in_taxa(child_leads, lead):
    if lead.taxa_cache:
        lead.taxa_rank, lead.taxa_list = lead.taxa_cache.split(':')
        lead.taxa_set = set(lead.taxa_list.split(','))
    elif child_leads.get(lead.id):
        children = child_leads.get(lead.id)
        lead.taxa_set = set()
        for child in children:
            fill_in_taxa(child_leads, child)
            lead.taxa_set.update(child.taxa_set)
        lead.taxa_rank = children[0].taxa_rank
        lead.taxa_list = ','.join(sorted(lead.taxa_set))
    else:
        lead.taxa_set = set()  # let the dkey display if cache is empty
        lead.taxa_rank = ''
        lead.taxa_list = []

class _Proxy(object):
    def __init__(self, page):
        self.set_page(page)

    def next(self):
        self.set_page(self.leads[0].goto_page)

    def set_page(self, page):
        self.page = page
        self.leads = (models.Lead.objects.filter(page=page)
                      .select_related('goto_page').all())

    def lead_hierarchy(self):
        leads = sorted(self.leads, key=models.Lead.sort_key)
        if not leads:
            return

        # Sort and group the leads.

        get_parent_id = attrgetter('parent_id')
        child_leads = {
            parent_id: list(group) for parent_id, group
            in groupby(leads, get_parent_id)
            }

        # Fill in taxa lists for non-leaf leads.

        for lead in reversed(leads):
            fill_in_taxa(child_leads, lead)

        # Yield the tree of leads.

        lead_depths = {None: 0}
        depth = 0

        for lead in leads:
            children = child_leads.get(lead.id)
            lead.nextnum = children[0].number if children else ''

            new_depth = lead_depths[lead.parent_id] + 1
            lead_depths[lead.id] = new_depth
            if depth < new_depth:
                id = ' id="c{}"'.format(lead.number)
                yield '<ul class="couplet"{}>'.format(id)
                depth += 1
            while depth > new_depth:
                yield '</ul>'
                depth -= 1
            yield '<li>'
            yield lead
            yield '</li>'

        while depth:
            yield '</ul>'
            depth -= 1

def get_groups():
    groups = []
    for number, text in group_texts_sorted:
        groups.append({'name': 'Group %d' % number, 'text': text})
    return groups

def get_families():
    pages = models.Page.objects.filter(rank='family')
    return sorted(page.title for page in pages)

def get_genera():
    pages = models.Page.objects.filter(rank='genus')
    return sorted(page.title for page in pages)

# Views

def family_groups(request):
    """Fake quite a few things to create a bare list of groups."""

    page = models.Page.objects.get(title='Key to the Families')
    page.title = 'List of Family Groups'
    proxy = _Proxy(page)

    leads = []
    lead_hierarchy = []

    for lead in proxy.lead_hierarchy():
        if not isinstance(lead, models.Lead):
            continue

        if not lead.goto_page:
            continue

        group_number = int(lead.goto_page.title.split()[1])
        lead.letter = str(group_number)
        lead.text = group_texts[group_number]

        leads.append(lead)

        lead_hierarchy.append('<li>')
        lead_hierarchy.append(lead)
        lead_hierarchy.append('</li>')

    return render_to_response('dkey/page.html', {
            'groups': get_groups,
            'families': get_families,
            'genera': get_genera,
            'leads': proxy.leads,
            'lead_hierarchy': lead_hierarchy,
            'page': page,
            }, context_instance=RequestContext(request))

def page(request, slug=u'key-to-the-families'):
    if slug != slug.lower():
        raise Http404
    title = slug.replace(u'-', u' ').capitalize().replace(
        ' families', ' Families').replace(' group ', ' Group ')
    page = get_object_or_404(models.Page, title=title)
    proxy = _Proxy(page)
    return render_to_response('dkey/page.html', {
            'groups': get_groups,
            'families': get_families,
            'genera': get_genera,
            'leads': (lambda: proxy.leads),
            'lead_hierarchy': (lambda: proxy.lead_hierarchy()),
            'next_page': (lambda: proxy.next() or proxy.page),
            'page': (lambda: proxy.page),
            }, context_instance=RequestContext(request))

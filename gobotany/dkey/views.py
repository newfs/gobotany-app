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

class _Proxy(object):
    def __init__(self, page):
        self.set_page(page)

    def next(self):
        self.set_page(self.leads[0].goto_page)

    def set_page(self, page):
        q = models.Lead.objects.filter(page=page).select_related('goto_page')
        self.leads = list(sorted(q, key=models.Lead.sort_key))
        self.page = page

        idmap = {lead.id: lead for lead in self.leads}
        tops = []

        for lead in self.leads:
            lead.childlist = []
            if lead.parent_id:
                parent = idmap[lead.parent_id]
                parent.childlist.append(lead)
                parent.child_couplet_number = lead.number()
            else:
                tops.append(lead)

        for lead in reversed(self.leads):
            if lead.taxa_cache:
                lead.taxa_rank, lead.taxa_list = lead.taxa_cache.split(':')
                lead.taxa_set = set(lead.taxa_list.split(','))
            else:
                lead.taxa_set = set()
                for child in lead.childlist:
                    lead.taxa_rank = child.taxa_rank
                    lead.taxa_set.update(child.taxa_set)
                lead.taxa_list = ','.join(sorted(lead.taxa_set))

        self.lead_hierarchy = []
        self.build_lead_hierarchy(tops, self.lead_hierarchy)

    def build_lead_hierarchy(self, leads, items):
        for lead in leads:
            items.append('<li>')
            items.append(lead)
            if lead.childlist:
                items.append('<ul id="c{}" class="couplet">'.format(
                        lead.child_couplet_number))
                self.build_lead_hierarchy(lead.childlist, items)
                items.append('</ul>')
            items.append('</li>')

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

# Our view.

def page(request, slug=u'key-to-the-families'):
    if slug != slug.lower():
        raise Http404
    title = slug.replace(u'-', u' ').capitalize().replace(
        ' families', ' Families').replace(' group ', ' Group ')
    if title.startswith('Tribe '):
        title = title.title()
    page = get_object_or_404(models.Page, title=title)
    proxy = _Proxy(page)
    return render_to_response('dkey/page.html', {
            'groups': get_groups,
            'families': get_families,
            'genera': get_genera,
            'leads': (lambda: proxy.leads),
            'lead_hierarchy': (lambda: proxy.lead_hierarchy),
            'next_page': (lambda: proxy.next() or proxy.page),
            'page': (lambda: proxy.page),
            }, context_instance=RequestContext(request))

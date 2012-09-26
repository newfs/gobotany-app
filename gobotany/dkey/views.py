from itertools import groupby
from operator import attrgetter

from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.dkey import models

group_texts = {
    1: 'Lycophytes, Monilophytes',
    2: 'Gymnosperms',
    3: 'Monocots',
    4: 'Woody angiosperms with opposite or whorled leaves',
    5: 'Woody angiosperms with alternate leaves',
    6: 'Herbaceous angiosperms with inferior ovaries',
    7: 'Herbaceous angiosperms with superior ovaries and zygomorphic flowers',
    8: 'Herbaceous angiosperms with superior ovaries, actinomorphic flowers,'
       ' and 2 or more distinct carpels',
    9: 'Herbaceous angiosperms with superior ovaries, actinomorphic flowers,'
       ' connate petals, and a solitary carpel or 2 or more connate carpels',
    10:'Herbaceous angiosperms with superior ovaries, actinomorphic flowers,'
       ' distinct petals or the petals lacking, and 2 or more connate carpels',
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
        leads = list(self.leads)
        if not leads:
            return

        # Sort and group all leads.

        get_parent_id = attrgetter('parent_id')
        leads.sort(key=models.Lead.sort_key)  # put 1a before 1b, etc
        leads = reversed(leads)  # since stack.pop() pulls from the end
        child_leads = {
            key: list(group) for key, group in groupby(leads, get_parent_id)
            }

        # Fill in taxa lists for non-leaf leads.

        for lead in child_leads[None]:
            fill_in_taxa(child_leads, lead)

        # Expand the leads into a full <ul> hierarchy.

        stack = []
        for child in child_leads[None]:
            stack += ['</li>', child, '<li>']
        while stack:
            item = stack.pop()
            if isinstance(item, basestring):
                yield item
                continue
            lead = item
            leads = child_leads.get(lead.id)
            if leads:
                lead.nextnum = leads[0].letter.strip('ab')
            yield lead
            if leads:
                stack += ['</ul>']
                for lead2 in leads:
                    stack += ['</li>', lead2, '<li>']
                id = ' id="c{}"'.format(lead.nextnum) if lead.nextnum else ''
                ul = '<ul class="couplet"{}>'.format(id)
                stack += [ul]  # TODO: needs id for linking

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

class FakePage(models.Page):
    @property
    def breadcrumb_cache(self):
        return models.Page.objects.none()

def family_groups(request):
    """Fake quite a few things to create a bare list of groups."""

    page = FakePage()
    page.title = 'List of Family Groups'
    proxy = _Proxy(page)
    proxy.leads = []
    for i, group in enumerate(models.Page.objects.filter(rank=u'group')):
        lead = models.Lead()
        lead.id = int(group.title.split()[-1])
        lead.letter = str(lead.id)
        lead.text = group_texts[lead.id]
        lead.goto_page = group
        proxy.leads.append(lead)
    proxy.leads.sort(key=attrgetter('id'))

    return render_to_response('dkey/page.html', {
            'leads': proxy.leads,
            'lead_hierarchy': proxy.lead_hierarchy(),
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

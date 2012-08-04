from itertools import groupby
from operator import attrgetter

from django.shortcuts import get_object_or_404, render_to_response
from gobotany.dkey import models

def lead_key(lead):
    """Return an appropriate sort key for the given lead."""
    return lead.letter

class OldProxy(object):
    def __init__(self, page):
        ids = [ int(n) for n in page.lead_ids.split(',') ]
        self.page = page
        self.leads = models.Lead.objects.filter(pk__in=ids).all()

    def has_only_one_lead(self):
        return 0
        return len(self.leads) == 1

    def first_lead(self):
        return self.leads[0]

    def step(self):
        self.couplet = self.couplet.leads[0].result_couplet
        return ''

    def leads(self):
        sequence = []
        for lead in sorted(self.couplet.leads.all(), key=lead_key):
            result = lead.result_couplet
            if result.title and result.title.startswith('go to couplet '):
                goto = result.title[14:]
            else:
                goto = None
            ranks_beneath = set()
            names_beneath = set()
            leads2 = sorted(result.leads.all(), key=lead_key)
            if leads2:
                number = leads2[0].letter[:-2]  # turn '12b.' into '12'
            else:
                number = 'NO NUMBER'
            couplets = [lead2.result_couplet for lead2 in leads2]
            already = set()

            while couplets:
                couplet = couplets.pop()
                already.add(couplet.id)
                if couplet.rank not in ('', 'group', 'subgroup', 'subkey'):
                    ranks_beneath.add(couplet.rank)
                    names_beneath.add(couplet.title)
                else:
                    for lead2 in couplet.leads.all():
                        result2 = lead2.result_couplet
                        if result2.id not in already:
                            couplets.append(result2)

            sequence.append((lead, result, number, goto,
                             sorted(ranks_beneath), sorted(names_beneath)))

        return sequence

class _Proxy(object):
    def __init__(self, page):
        self.set_page(page)

    def next(self):
        self.set_page(self.leads[0].goto_page)

    def set_page(self, page):
        self.page = page
        if page.lead_ids:
            lead_ids = [ int(n) for n in page.lead_ids.split(u',') ]
        else:
            lead_ids = []
        self.leads = models.Lead.objects.filter(pk__in=lead_ids).all()

    def lead_hierarchy(self):
        if not self.leads:
            return
        get_parent_id = attrgetter('parent_id')
        leads = sorted(self.leads, key=get_parent_id)  # groupby needs sort
        leads = reversed(leads)  # since stack.pop() pulls from the end
        child_leads = {
            key: list(group) for key, group in groupby(leads, get_parent_id)
            }
        stack = []
        for child in child_leads[None]:
            stack += ['</li>', child, '<li>']
        while stack:
            item = stack.pop()
            yield item
            if isinstance(item, basestring):
                continue
            children = child_leads.get(item.id)
            if children:
                stack += ['</ul>']
                for child in children:
                    stack += ['</li>', child, '<li>']
                stack += ['<ul>']

def get_families():
    pages = models.Page.objects.filter(rank='family')
    return sorted(page.title for page in pages)

def get_genera():
    pages = models.Page.objects.filter(rank='genus')
    return sorted(page.title for page in pages)

def index(request):
    return render_to_response('dkey/index.html')

def page(request, slug):
    title = slug.replace(u'-', u' ')
    page = get_object_or_404(models.Page, title=title)
    proxy = _Proxy(page)
    return render_to_response('dkey/page.html', {
            'families': get_families,
            'genera': get_genera,
            'leads': (lambda: proxy.leads),
            'lead_hierarchy': (lambda: proxy.lead_hierarchy()),
            'next_page': (lambda: proxy.next() or proxy.page),
            'page': (lambda: proxy.page),
            })

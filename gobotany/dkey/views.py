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

class _Proxy(object):
    def __init__(self, page):
        self.set_page(page)

    def next(self):
        self.set_page(self.leads[0].goto_page)

    def set_page(self, page):
        self.page = page
        if page.lead_ids:
            lead_ids = [ int(n) for n in page.lead_ids.split(u',') ]
            self.leads = (models.Lead.objects.filter(pk__in=lead_ids)
                          .select_related('goto_page').all())
        else:
            self.leads = []

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
            if isinstance(item, basestring):
                yield item
                continue
            leads = child_leads.get(item.id)
            if leads:
                item.nextnum = leads[0].letter.strip('ab')
            yield item
            if leads:
                stack += ['</ul>']
                for lead in leads:
                    stack += ['</li>', lead, '<li>']
                id = ' id="c{}"'.format(item.nextnum) if item.nextnum else ''
                ul = '<ul class="couplet"{}>'.format(id)
                stack += [ul]  # TODO: needs id for linking

def get_families():
    pages = models.Page.objects.filter(rank='family')
    return sorted(page.title for page in pages)

def get_genera():
    pages = models.Page.objects.filter(rank='genus')
    return sorted(page.title for page in pages)

# Views

def family_groups(request):
    """Fake quite a few things to create a bare list of groups."""

    page = models.Page()
    page.title = 'List of Family Groups'
    proxy = _Proxy(page)
    for group in models.Page.objects.filter(rank=u'group').all():
        lead = models.Lead()
        lead.id = int(group.title.split()[-1])
        lead.letter = 'Group {}'.format(lead.id)
        lead.text = group_texts[lead.id]
        lead.goto_page = group
        proxy.leads.append(lead)
    proxy.leads.sort(key=attrgetter('id'))

    return render_to_response('dkey/page.html', {
            'leads': proxy.leads,
            'lead_hierarchy': proxy.lead_hierarchy(),
            'page': page,
            })

def page(request, slug=u'Key-to-the-Families'):
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

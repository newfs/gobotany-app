from django.shortcuts import get_object_or_404, render_to_response
from gobotany.dkey.models import Couplet

def lead_key(lead):
    """Return an appropriate sort key for the given lead."""
    return lead.letter

class Proxy(object):
    def __init__(self, couplet):
        self.couplet = couplet

    def has_only_one_lead(self):
        return len(self.couplet.leads) == 1

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

def index(request):
    return render_to_response('dkey/index.html')

def couplet(request, couplet_slug):
    title = couplet_slug.replace('-', ' ')
    couplet = get_object_or_404(Couplet, title=title)
    return render_to_response('dkey/couplet.html', {
            'couplet': couplet,
            'proxy': Proxy(couplet),
            })

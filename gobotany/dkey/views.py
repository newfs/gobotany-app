from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.core.models import Taxon, ContentImage
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
                lead.rank_beneath, commalist = lead.taxa_cache.split(':')
                lead.taxa_beneath = set(commalist.split(','))
            else:
                lead.taxa_beneath = set()
                for child in lead.childlist:
                    lead.rank_beneath = child.rank_beneath
                    lead.taxa_beneath.update(child.taxa_beneath)

        self.rank_beneath = tops[0].rank_beneath if tops else ''
        self.taxa_beneath = set().union(*(lead.taxa_beneath for lead in tops))

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

    def get_image_collection(self):

        # Our first task is to produce a "titlemap" whose keys are
        # species IDs whose images we want fetched, and whose values are
        # the titles that we will attach. When illustrating species or
        # genera we can just use the scientific name, since it includes
        # the genus, but when illustrating families we also include the
        # family name.

        ctype = ContentType.objects.get_for_model(Taxon)

        if self.rank_beneath == u'family':

            cursor = connection.cursor()
            cursor.execute("""
                SELECT f.name,
                  (SELECT id FROM core_taxon WHERE family_id = f.id LIMIT 1)
                  FROM core_family f
                  WHERE f.name IN %s""", (tuple(self.taxa_beneath),))
            family_name_map = {taxon_id: family_name
                               for family_name, taxon_id in cursor.fetchall()}

            ids = family_name_map.keys()
            images = (ContentImage.objects.select_related('image_type')
                      .filter(content_type=ctype, object_id__in=ids, rank=1))

            titles_and_images = sorted(
                ('{}<br><i>({})</i>'.format(family_name_map[image.object_id],
                                            image.alt.split(':')[0]),
                 image) for image in images
                )
            return titles_and_images

        if self.rank_beneath == u'genus':

            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                  (SELECT id FROM core_taxon WHERE genus_id = g.id LIMIT 1)
                  FROM core_genus g
                  WHERE g.name IN %s""", (tuple(self.taxa_beneath),))
            ids = (row[0] for row in cursor.fetchall())

        elif self.rank_beneath == u'species':
            taxa = Taxon.objects.filter(scientific_name__in=self.taxa_beneath)
            ids = (taxon.id for taxon in taxa)

        else:
            return []

        images = (ContentImage.objects.select_related('image_type')
                  .filter(content_type=ctype, object_id__in=ids, rank=1))
        titles_and_images = sorted(
            ('<i>{}</i>'.format(image.alt.split(':')[0]), image)
            for image in images
            )
        return titles_and_images

def get_groups():
    groups = []
    for number, text in group_texts_sorted:
        groups.append({'name': 'Group %d' % number, 'text': text})
    return groups

# Our view.

def page(request, slug=u'key-to-the-families'):
    if slug != slug.lower():
        raise Http404
    title = models.slug_to_title(slug)
    if title.startswith('Tribe '):
        title = title.title()
    page = get_object_or_404(models.Page, title=title)
    proxy = _Proxy(page)
    return render_to_response('dkey/page.html', {
            'groups': get_groups,

            'leads': (lambda: proxy.leads),
            'lead_hierarchy': (lambda: proxy.lead_hierarchy),
            'page': (lambda: proxy.page),
            'rank_beneath': (lambda: proxy.rank_beneath),
            'taxa_beneath': (lambda: proxy.taxa_beneath),
            'image_collection': (lambda: proxy.get_image_collection()),

            'next_page': (lambda: proxy.next() or proxy.page),
            }, context_instance=RequestContext(request))

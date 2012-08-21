"""Bring database models up to date."""

from operator import attrgetter

from gobotany import settings
from django.core import management
management.setup_environ(settings)

from django.db import connection, transaction
from gobotany.dkey import models

def is_major_taxon(page):
    return page.rank in ('family', 'genus', 'species')

def cache_taxon(pagedict, leadindict, rank, taxon, page):
    """Tell the leads leading to `page` that `rank` `taxon` is below them.

    For example, 1a on the first page will be told that the "Family"
    "Aspleniaceae" lies somewhere beneath it.  By the time this routine
    has been called on all of the pages below the root, 1a will know
    about all 21 families that can be reached through the decision trees
    below it.

    """
    for leadin in leadindict[page.id]:
        if not leadin.taxa_cache:
            leadin.taxa_cache = (rank, set())  # turned into str before save()
        leadin.taxa_cache[1].add(taxon)
        page2 = pagedict[leadin.page_id]
        if not is_major_taxon(page2):
            cache_taxon(pagedict, leadindict, rank, taxon, page2)

@transaction.commit_on_success
def sync():
    """Update the breadcrumbs and taxa caches."""

    # Start fresh.

    c = connection.cursor()
    c.execute("DELETE FROM dkey_page_breadcrumb_cache")
    c.execute("UPDATE dkey_lead SET taxa_cache = ''")

    # Load pages.

    pagelist = list(models.Page.objects.all())
    pagedict = { page.id: page for page in pagelist }
    leadindict = { page.id: list(page.leadins.all()) for page in pagelist }
    parents = {}
    idgetter = attrgetter('id')

    # Follow leads to learn which pages are parents to which other pages.

    for page in pagelist:
        leadins = leadindict[page.id]
        if leadins:
            leadins.sort(key=idgetter)
            parents[page] = pagedict[leadins[0].page_id]

    # Rebuild the caches.

    for page in pagelist:
        parent = parents.get(page)
        while parent is not None:
            page.breadcrumb_cache.add(parent)
            parent = parents.get(parent)

        if is_major_taxon(page):
            cache_taxon(pagedict, leadindict, page.rank, page.title, page)

    for leadins in leadindict.values():
        for leadin in leadins:
            tc = leadin.taxa_cache
            leadin.taxa_cache = '{}:{}'.format(tc[0], ','.join(sorted(tc[1])))
            leadin.save()  # save the new `taxa_cache` strings

if __name__ == '__main__':
    sync()

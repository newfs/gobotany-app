"""Bring database models up to date."""

from operator import attrgetter

from gobotany import settings
from django.core import management
management.setup_environ(settings)

from django.db import transaction
from gobotany.dkey import models

@transaction.commit_on_success
def sync():
    """Update the cache of which pages have which ancestors."""

    pages = { page.id: page for page in models.Page.objects.all() }
    parents = {}
    idgetter = attrgetter('id')

    for page in pages.values():
        page.ancestors.clear()

    for page in pages.values():
        leads = list(page.leadins.all())
        if leads:
            leads.sort(key=idgetter)
            parents[page] = pages[leads[0].page_id]

    for page in pages.values():
        parent = parents.get(page)
        while parent is not None:
            page.ancestors.add(parent)
            parent = parents.get(parent)

if __name__ == '__main__':
    sync()

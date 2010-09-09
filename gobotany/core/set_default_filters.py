"""Compute the best characters for each pile, make them the default filters."""

import time

from django.core import management
from gobotany import settings
management.setup_environ(settings)

from gobotany.core import igdt, models

DEFAULT_FILTERS_PER_PILE = 3

def main():
    for pile in models.Pile.objects.all():
        print "Pile", pile.name

        old_filters = pile.default_filters.all()
        print "  Removing %d old default filters" % len(old_filters)
        old_filters.delete()

        print "  Computing new 'best' filters"
        t = time.time()
        result = igdt.rank_characters(pile, list(pile.species.all()))
        print "  Computation took %.3f seconds" % (time.time() - t)

        print "  Inserting new 'best' filters"
        result = result[:DEFAULT_FILTERS_PER_PILE]
        for n, (score, entropy, coverage, character) in enumerate(result):
            print "   ", character.name
            defaultfilter = models.DefaultFilter()
            defaultfilter.pile = pile
            defaultfilter.character = character
            defaultfilter.order = n
            defaultfilter.save()

if __name__ == '__main__':
    main()

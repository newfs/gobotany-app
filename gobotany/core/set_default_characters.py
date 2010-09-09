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
        for f in old_filters:
            pile.default_filters.remove(f)

        print "  Computing new 'best' filters"
        t = time.time()
        result = igdt.rank_characters(pile, list(pile.species.all()))
        print "  Computation took %.3f seconds" % (time.time() - t)

        print "  Inserting new 'best' filters"
        result = result[:DEFAULT_FILTERS_PER_PILE]
        for score, entropy, coverage, character in result:
            print "   ", character.name
            print dir(pile.default_filters)
            pile.default_filters.add(character)

if __name__ == '__main__':
    main()

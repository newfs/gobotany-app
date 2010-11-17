"""Rebuild parts of our database that we generate rather than import."""

import random
import sys
import time
from itertools import chain

from django.core import management
from gobotany import settings
management.setup_environ(settings)
from gobotany.core import igdt, models


DEFAULT_FILTERS_PER_PILE = 3

def rebuild_default_filters():
    """Rebuild default-filters for every pile, choosing 'best' characters."""
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


SAMPLE_IMAGES_PER_PILE = 6

def rebuild_sample_pile_images():
    """Randomly assign sample species images to each pilegroup and pile."""
    for p in chain(models.Pile.objects.all(),
                      models.PileGroup.objects.all()):
        print '%-26s -' % (type(p).__name__ + ' ' + p.name),

        old_images = p.sample_species_images.all()
        if len(old_images):
            print "removing %d old images;" % len(old_images),
            for image in old_images:
                p.sample_species_images.remove(image)

        piles = [p] if isinstance(p, models.Pile) else p.piles.all()
        image_list = []
        for pile in piles:
            for species in pile.species.all():
                image_list.extend(list(species.images.filter(
                    image_type__name='habit')))

        if len(image_list) > SAMPLE_IMAGES_PER_PILE:
            image_list = random.sample(image_list, SAMPLE_IMAGES_PER_PILE)

        print "inserting %d random images" % len(image_list)

        for image in image_list:
            p.sample_species_images.add(image)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, "Usage: rebuild THING"
        exit(2)
    thing = sys.argv[1]
    function_name = 'rebuild_' + thing
    if function_name in globals():
        function = globals()[function_name]
        function()
    else:
        print >>sys.stderr, "Error: rebuild target %r unknown" % thing
        exit(2)

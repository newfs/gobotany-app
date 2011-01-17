"""Rebuild parts of our database that we generate rather than import."""

import csv
import os
import random
import sys
import time
from itertools import chain

from django.core import management
from django.core.exceptions import ObjectDoesNotExist

from gobotany import settings
management.setup_environ(settings)
from gobotany.core import igdt, models


DEFAULT_BEST_FILTERS_PER_PILE = 3


class CSVReader(object):

    def __init__(self, filename):
        self.filename = filename

    def read(self):
        # Open in universal newline mode in order to deal with newlines in
        # CSV files saved on Mac OS.
        with open(self.filename, 'rU') as f:
            r = csv.reader(f, dialect=csv.excel, delimiter=',')
            for row in r:
                yield [c.decode('Windows-1252') for c in row]


def rebuild_default_filters():
    """Rebuild default-filters for every pile, choosing 'best' characters."""
    for pile in models.Pile.objects.all():
        print "Pile", pile.name

        old_filters = pile.default_filters.all()
        print "  Removing %d old default filters" % len(old_filters)
        old_filters.delete()

        common_filter_character_names = ['habitat', 'state_distribution']
        print "  Inserting 'common' filters"
        for n, character_name in enumerate(common_filter_character_names):
            try:
                character = models.Character.objects.get( \
                    short_name=character_name)
            except models.Character.DoesNotExist:
                print "Error: Character does not exist: %s" % character_name
                continue
            print "   ", character.name
            defaultfilter = models.DefaultFilter()
            defaultfilter.pile = pile
            defaultfilter.character = character
            defaultfilter.order = n
            defaultfilter.save()

        print "  Computing new 'best' filters"
        t = time.time()
        result = igdt.rank_characters(pile, list(pile.species.all()))
        print "  Computation took %.3f seconds" % (time.time() - t)

        print "  Inserting new 'best' filters"
        number_of_filters_to_evaluate = DEFAULT_BEST_FILTERS_PER_PILE + \
            len(common_filter_character_names)
        result = result[:number_of_filters_to_evaluate]
        number_added = 0
        for n, (score, entropy, coverage, character) in enumerate(result):
            # Skip any 'common' filters if they come up in the 'best' filters,
            # because they've already been added.
            if (character.short_name not in common_filter_character_names):
                print "   ", character.name
                defaultfilter = models.DefaultFilter()
                defaultfilter.pile = pile
                defaultfilter.character = character
                defaultfilter.order = n + len(common_filter_character_names)
                defaultfilter.save()
                number_added += 1
                # If no more filters need to be added, stop now.
                if number_added == DEFAULT_BEST_FILTERS_PER_PILE:
                    break;


def rebuild_sample_pile_images(pile_or_group_csv_1, pile_or_group_csv_2):
    """Assign sample species images to each pile group and pile."""
    print 'Rebuild sample pile images:'

    print '  Removing old images:'
    for p in chain(models.PileGroup.objects.all(),models.Pile.objects.all()):
        print '    ', (type(p).__name__ + ': ' + p.name),
        old_images = p.sample_species_images.all()
        if len(old_images):
            print '      removing %d old images' % len(old_images)
            for image in old_images:
                p.sample_species_images.remove(image)
        else:
            print '      none'

    print '  Adding images from CSV data:'
    files = [pile_or_group_csv_1, pile_or_group_csv_2]
    for f in files:
        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = dict(zip(colnames, cols))
            # Skip junk rows.
            if row['name'].lower() == 'all' or \
               row['name'].lower() == 'unused':
                continue

            image_list = []
            try:
                p = models.PileGroup.objects.get(name=row['name'])
                print '    PileGroup:', p.name
                for pile in p.piles.all():
                    for species in pile.species.all():
                        image_list.extend(list(species.images.all()))
            except ObjectDoesNotExist:
                p = models.Pile.objects.get(name=row['name'].title())
                print '    Pile:', p.name
                for species in p.species.all():
                    image_list.extend(list(species.images.all()))

            image_filenames = row['image_filenames'].split(';')
            for filename in image_filenames:
                # Skip malformed filenames.
                if not filename.lower().endswith('.jpg'):
                    continue
                print '      filename:', filename,
                found = False
                for image_instance in image_list:
                    if image_instance.image.name.find(filename) > -1:
                        p.sample_species_images.add(image_instance)
                        found = True
                        break   # Found image, so no need to continue the loop.
                if found:
                    print '- found, added'
                else:
                    print '- not found'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: rebuild THING {args}"
        exit(2)
    thing = sys.argv[1]
    function_name = 'rebuild_' + thing
    if function_name in globals():
        function = globals()[function_name]
        function(*sys.argv[2:])
    else:
        print >>sys.stderr, "Error: rebuild target %r unknown" % thing
        exit(2)

"""Rebuild parts of our database that we generate rather than import."""

import csv
import sys
import time

from django.core import management
from django.core.exceptions import ObjectDoesNotExist

from gobotany import settings
management.setup_environ(settings)
from gobotany.core import igdt, importer, models
from gobotany.plantoftheday.models import PlantOfTheDay

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

def _add_best_filters(pile, common_filter_character_names):
    print "  Computing new 'best' filters"
    t = time.time()
    result = igdt.rank_characters(pile, list(pile.species.all()))
    print "  Computation took %.3f seconds" % (time.time() - t)

    print "  Inserting new 'best' filters:"
    DEFAULT_BEST_FILTERS_PER_PILE = 3
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
                break


def rebuild_default_filters(characters_csv):
    """Rebuild default filters for every pile, using CSV data where
       available or choosing 'best' characters otherwise.
    """
    for pile in models.Pile.objects.all():
        print "Pile", pile.name

        old_filters = pile.default_filters.all()
        print "  Clearing %d old default filters" % len(old_filters)
        # Just clear the old filters rather than deleting them, so as to not
        # have a delete-cascade that also deletes character records.
        pile.default_filters.clear()

        COMMON_FILTER_CHARACTER_NAMES = ['habitat_general',
                                         'state_distribution']
        print "  Inserting common filters:"
        for n, character_name in enumerate(COMMON_FILTER_CHARACTER_NAMES):
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

        # Look for default filters specified in the CSV data. If not found,
        # add some next 'best' filters instead.
        default_filter_characters = importer.get_default_filters_from_csv(
            pile.name, characters_csv)
        if len(default_filter_characters) > 0:
            print "  Inserting new default filters from CSV data:"
            for n, character in enumerate(default_filter_characters):
                print "   ", character.name
                defaultfilter = models.DefaultFilter()
                defaultfilter.pile = pile
                defaultfilter.character = character
                defaultfilter.order = n + len(COMMON_FILTER_CHARACTER_NAMES)
                defaultfilter.save()
        else:
            _add_best_filters(pile, COMMON_FILTER_CHARACTER_NAMES)


def _remove_sample_species_images(pile_or_group_model):
    """Remove any sample species_images from all piles or all pile groups."""
    print '  Removing old images:'
    for pile in pile_or_group_model.objects.all():
        print '    %s ' % pile.name
        old_images = pile.sample_species_images.all()
        if len(old_images):
            print '      removing %d old images' % len(old_images)
            pile.sample_species_images.clear()
        else:
            print '      none'


def _extend_image_list(image_list, pile):
    """For each species in a pile, extend an image list with all images."""
    for species in pile.species.all():
        image_list.extend(list(species.images.all()))
    return image_list


def rebuild_sample_pile_group_images(pilegroup_csv):
    """Assign sample species images to each pile group."""

    print 'Rebuild sample pile group images:'
    _remove_sample_species_images(models.PileGroup)

    print '  Adding images from CSV data:'
    iterator = iter(CSVReader(pilegroup_csv).read())
    colnames = [c.lower() for c in iterator.next()]
    for cols in iterator:
        row = dict(zip(colnames, cols))
        # Skip junk rows.
        if row['name'].lower() in ['all', 'unused']:
            continue

        # Build a list of all species images in the pile group.
        image_list = []
        pile_group = models.PileGroup.objects.get(name=row['name'])
        print '    PileGroup:', pile_group.name
        # Extend the image list with the list of all species images for
        # all piles in the group.
        for pile in pile_group.piles.all():
            _extend_image_list(image_list, pile)

        # Go through the image filenames specified in the CSV data and
        # look for them in the image list. If found, add them to the
        # pile group as sample species images.
        image_filenames = row['image_filenames'].split(';')
        for filename in image_filenames:
            # Skip malformed filenames.
            if not filename.lower().endswith('.jpg'):
                continue
            print '      filename:', filename,
            found = False
            message = ''
            for image_instance in image_list:
                if image_instance.image.name.find(filename) > -1:
                    sample_species_image = models.PileGroupImage(
                        content_image=image_instance,
                        pile_group=pile_group)
                    sample_species_image.save()
                    # Set an ordering field, editable in the Admin.
                    sample_species_image.order = sample_species_image.id
                    sample_species_image.save()
                    found = True
                    break
            if found:
                print '- found, added to pile group'
            else:
                print '- not found'


def rebuild_sample_pile_images(pile_csv):
    """Assign sample species images to each pile."""

    print 'Rebuild sample pile images:'
    _remove_sample_species_images(models.Pile)

    print '  Adding images from CSV data:'
    iterator = iter(CSVReader(pile_csv).read())
    colnames = [c.lower() for c in iterator.next()]

    for cols in iterator:
        row = dict(zip(colnames, cols))
        # Skip junk rows.
        if row['name'].lower() in ['all', 'unused']:
            continue

        # Build a list of all species images in the pile.
        image_list = []
        p = models.Pile.objects.get(name=row['name'].title())
        print '    Pile:', p.name
        # Extend the image list with the list of all species images for
        # the pile.
        _extend_image_list(image_list, p)

        # Go through the image filenames specified in the CSV data and
        # look for them in the image list. If found, add them to the
        # pile as sample species images.
        image_filenames = row['image_filenames'].split(';')
        for filename in image_filenames:
            # Skip malformed filenames.
            if not filename.lower().endswith('.jpg'):
                continue
            print '      filename:', filename,
            found = False
            message = '- not found'
            for image_instance in image_list:
                if image_instance.image.name.find(filename) > -1:
                    found = True
                    sample_species_image = models.PileImage(
                        content_image=image_instance, pile=p)
                    sample_species_image.save()
                    # Set an ordering field, editable in the Admin.
                    sample_species_image.order = sample_species_image.id
                    sample_species_image.save()
                    message = '- found, added to pile'
                    # Add the image to the pile's group, if it hasn't
                    # already been added there.
                    try:
                        if p.pilegroup:
                            image_found = False
                            for i in p.pilegroup.sample_species_images.all():
                                if i.image.name == image_instance.image.name:
                                    image_found = True
                                    break
                            if not image_found:
                                sample_species_image = models.PileGroupImage(
                                    content_image=image_instance,
                                    pile_group=p.pilegroup)
                                sample_species_image.save()
                                sample_species_image.order = \
                                    sample_species_image.id
                                sample_species_image.save()
                                message += ', and added to pile group ' + \
                                    p.pilegroup.name
                    except AttributeError:
                        pass
                    break
            print message


def rebuild_plant_of_the_day(include_plants='SIMPLEKEY'):   # or 'ALL'
    """Rebuild the Plant of the Day list without wiping it out.

    This means that plant data can be reloaded and the Plant of the Day
    list then updated to include the current list of plants, minus any
    exclusions. This will ensure any new plants (or those with changed
    names) make it into the list.

    Any records in the list that do not have their last_modified field
    showing the latest rebuild date are likely old and should be deleted.
    For now, this is left as an occasional manual maintenance task.
    """
    if include_plants not in ['SIMPLEKEY', 'ALL']:
        print '  Unknown include_plants value: %s' % include_plants
    else:
        print '  Rebuilding Plant of the Day list (%s):' % include_plants
        for partner_site in models.PartnerSite.objects.all():
            print '    Partner site: %s' % partner_site
            species = models.PartnerSpecies.objects.filter(
                partner=partner_site)
            if include_plants == 'SIMPLEKEY':
                species = species.filter(simple_key=True)
            for s in species:
                try:
                    potd = PlantOfTheDay.objects.get(
                        scientific_name=s.species.scientific_name,
                        partner_short_name=s.partner.short_name)
                    # Save the existing record so its last_updated field
                    # will be updated.
                    potd.save()
                except ObjectDoesNotExist:
                    # Create a new Plant of the Day record.
                    potd = PlantOfTheDay(
                        scientific_name=s.species.scientific_name,
                        partner_short_name=s.partner.short_name)
                    potd.save()


def rebuild_thumbnails():
    # Rebuild content-image thumbnails.
    cis = models.ContentImage.objects.all()
    for i, ci in enumerate(cis):
        j = i + 1
        print '\r%20d/%d  %6.2f%%' % (j, len(cis), 100.0 * j / len(cis)),
        ci.thumb_small()
        ci.thumb_large()
        ci.image_medium()


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

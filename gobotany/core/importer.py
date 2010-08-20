from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from gobotany import settings
management.setup_environ(settings)

import csv
import os
import re
import sys
import tarfile
from gobotany.core import models
from django.contrib.contenttypes.models import ContentType

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

pile_mapping = {
    'ca': u'Carex',
    'co': u'Composites',
    'eq': u'Equisetaceae',
    'ly': u'Lycophytes',
    'mo': u'Monilophytes',
    'nm': u'Non-orchid monocots',
    'ap': u'Non-thalloid aquatic',
    'om': u'Orchid monocots',
    'po': u'Poaceae',
    'rg': u'Remaining graminoids',
    'rn': u'Remaining non-monocots',
    'ta': u'Thalloid aquatic',
    #'': u'Woody Angiosperms',
    #'': u'Woody Gymnosperms',
    }

class Importer(object):

    def __init__(self, logfile=sys.stdout):
        self.logfile = logfile

    def import_data(self, pilef, pile_images, taxaf, charf, charvf,
                    char_glossaryf, glossaryf, glossary_images,
                    *taxonfiles):
        self._import_piles(pilef, pile_images)
        self._import_taxa(taxaf)
        self._import_characters(charf)
        self._import_character_values(charvf)
        self._import_character_glossary(char_glossaryf)
        self._import_glossary(glossaryf, glossary_images)
        self._import_default_filters()
        self._import_plant_preview_characters()
        self._import_extra_demo_data()
        for taxonf in taxonfiles:
            self._import_taxon_character_values(taxonf)

    def _add_pile_images(self, pile, images, prefix_mapping):
        """Adds images for a pile or pile group"""
        # Create the two image types relevant for piles
        filter_type, created = models.ImageType.objects.get_or_create(
            name='filter drawing')
        pile_type, created = models.ImageType.objects.get_or_create(
            name='pile image')

        found_rank_one = False
        for filename in prefix_mapping.get(
            pile.name.lower().replace('-',' ').replace('(','').replace(')',''),
            ()):
            parts = filename.split('-')
            image_type = filter_type if (parts[-2] == 'filter') else pile_type
            # XXX: arbitrarily set a default image
            if image_type == pile_type and not found_rank_one:
                rank = 1
                found_rank_one = True
            else:
                # Everything else has the same rank
                rank = 2
            content_image, created = models.ContentImage.objects.get_or_create(
                rank=rank,
                alt = '%s %s: %s'%(pile.name, image_type.name,
                                   filename),
                image_type=image_type,
                object_id=pile.pk,
                content_type=ContentType.objects.get_for_model(pile))
            if created:
                image_file = File(images.extractfile(filename))
                content_image.image.save(filename, image_file)
                content_image.save()
                print >> self.logfile, u'    Added Pile Image:', filename

    def _import_piles(self, pilef, pile_images):
        print >> self.logfile, 'Setting up pile groups and piles'
        iterator = iter(CSVReader(pilef).read())
        colnames = [x.lower() for x in iterator.next()]

        if pile_images:
            pile_images = tarfile.open(pile_images)
            # Generate a mapping of pile-name to filenames from the image
            # tarball
            pile_prefixes = {}
            for image in pile_images:
                if image.name.startswith('.'):
                    continue
                image_name, image_ext = image.name.split('.')
                if image_ext.lower() not in ('jpg', 'gif', 'png', 'tif'):
                    # not an image
                    continue
                parts = image_name.split('-')
                prefix = ' '.join(parts[:-2])
                names = pile_prefixes.setdefault(prefix, [])
                names.append(image.name)

        for cols in iterator:
            row = dict(zip(colnames, cols))
            # Skip the 'All' pile
            if row['name'].lower() == 'all':
                continue

            pilegroup = None
            # If a Pile Group is specified, create it if doesn't exist yet.
            if row['pile_group']:
                pilegroup, created = models.PileGroup.objects.get_or_create(
                    name=row['pile_group'].title())
                # TODO: Are friendly_name and description important to set for
                # a Pile Group? (The schema allows for them.) If so, will need
                # to decide how to obtain those values.
                if created:
                    print >> self.logfile, u'  New PileGroup:', pilegroup
                if pile_images:
                    self._add_pile_images(pilegroup, pile_images, pile_prefixes)

            # Create the Pile.
            pile, created = models.Pile.objects.get_or_create(
                name=row['name'].title())
            pile.pilegroup = pilegroup
            # Update the friendly name and description.
            pile.friendly_name = row['friendly_name']
            pile.description = row['description']
            pile.save()
            if pile_images:
                self._add_pile_images(pile, pile_images, pile_prefixes)
            if created:
                print >> self.logfile, u'    New Pile:', pile
            else:
                print >> self.logfile, u'    Updated Pile:', pile

    def _import_taxa(self, taxaf):
        print >> self.logfile, 'Setting up taxa'
        iterator = iter(CSVReader(taxaf).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            # Find the family and genus.
            family, created = models.Family.objects.get_or_create(
                name=row['family'])
            genus, created = models.Genus.objects.get_or_create(
                name=row['scientific_name'].split()[0])

            # Create a Taxon.
            taxon = models.Taxon(
                scientific_name=row['scientific_name'],
                family=family,
                genus=genus,
                taxonomic_authority = row['taxonomic_authority'],
                simple_key = (row['simple_key'] == 'TRUE'),
                )
            taxon.save()
            print >> self.logfile, u'    New Taxon:', taxon

            # Assign this Taxon to the Pile(s) specified for it.
            if row['pile']:
                for pile_name in re.split(r'[,;]', row['pile']):
                    # Look for a Pile with this name.
                    piles = models.Pile.objects.filter(
                        name__iexact=pile_name.strip())
                    if piles:
                        pile = piles[0]
                        pile.species.add(taxon)
                    else:
                        print >> self.logfile, u'      CANNOT FIND PILE:', \
                            pile_name

    def _import_taxon_character_values(self, f):
        print >> self.logfile, 'Setting up taxon character values'
        iterator = iter(CSVReader(f).read())
        colnames = list(iterator.next())  # do NOT lower(); case is important

        _pile_suffix = colnames[-2][-3:]  # like '_ca'
        pile_suffix = _pile_suffix[1:]   # like 'ca'
        if pile_suffix not in pile_mapping:
            print >> self.logfile, "Pile '%s' isn't mapped" % pile_suffix
            return

        pile = models.Pile.objects.get(name__iexact=pile_mapping[pile_suffix])

        for cols in iterator:
            row = dict(zip(colnames, cols))

            # Look up the taxon and if it exists, import character values.
            taxa = models.Taxon.objects.filter(
                scientific_name__iexact=row['Scientific_Name'])
            if not taxa:
                continue
            taxon = taxa[0]

            for k, v in row.items():
                if not v.strip():
                    continue
                if not k.endswith(_pile_suffix):  # '_ca' or whatever
                    continue

                cname = k[:-3]
                is_min = cname.lower().endswith('_min')
                is_max = cname.lower().endswith('_max')
                if is_min or is_max:
                    cname = cname[:-4]

                try:
                    character = models.Character.objects.get(short_name=cname)
                except ObjectDoesNotExist:
                    print >> self.logfile, 'No such character exists: %s'%cname
                    continue

                if is_min or is_max:

                    try:
                        intv = int(v)
                    except ValueError:
                        print >> self.logfile, 'Not an int: %s=%s' % (cname, v)
                        continue

                    # Min and max get stored in the same char-value row.
                    tcvs = models.TaxonCharacterValue.objects.filter(
                        taxon=taxon,
                        character_value__character=character,
                        ).all()
                    if tcvs:
                        cv = tcvs[0].character_value
                    else:
                        cv = models.CharacterValue(character=character)
                        cv.save()
                        pile.character_values.add(cv)
                        models.TaxonCharacterValue(
                            taxon=taxon, character_value=cv).save()

                    if is_min:
                        cv.value_min = intv
                    else:
                        cv.value_max = intv
                    cv.save()

                else:
                    # A regular comma-separated list of string values.
                    for val in v.split(','):
                        val = val.strip()
                        cv, created = models.CharacterValue \
                            .objects.get_or_create(value_str=val,
                                                   character=character)
                        cv.save()
                        pile.character_values.add(cv)
                        models.TaxonCharacterValue.objects.get_or_create(
                            taxon=taxon, character_value=cv)

    def _import_characters(self, f):
        print >> self.logfile, 'Setting up characters'
        iterator = iter(CSVReader(f).read())
        colnames = [ x.lower() for x in iterator.next() ]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            if '_' not in row['character']:
                continue # ignore "family" rows for right now
            short_name, pile_suffix = row['character'].rsplit('_', 1)

            # Detect lengths and set the short_name and value_type properly
            if short_name.endswith('_min') or short_name.endswith('_max'):
                short_name = short_name[:-4]
                value_type = 'LENGTH'
            else:
                value_type = 'TEXT'

            chargroup, created = models.CharacterGroup.objects.get_or_create(
                name=row['character_group'])
            if created:
                print >> self.logfile, u'    New Character Group:', \
                    chargroup.name

            eoo = row['ease_of_observability']
            eoo = int(eoo)
            res = models.Character.objects.filter(short_name=short_name)
            if len(res) == 0:
                print >> self.logfile, u'      New Character: ' + short_name
                # Create a friendly name automatically for now.
                temp_friendly_name = short_name.replace('_', ' ').capitalize()
                character = models.Character(short_name=short_name,
                                             name=temp_friendly_name,
                                             friendly_name=temp_friendly_name,
                                             character_group=chargroup,
                                             value_type=value_type,
                                             ease_of_observability=eoo)
                character.save()

    def _import_character_values(self, f):
        print >> self.logfile, 'Setting up character values'
        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            if '_' not in row['character']:
                continue # ignore "family" rows for right now
            short_name, pile_suffix = row['character'].rsplit('_', 1)

            # Detect lengths and set the short_name properly
            if short_name.endswith('_min') or short_name.endswith('_max'):
                short_name = short_name[:-4]

            # only handling the two _ly and _ca piles for now
            if not pile_suffix in pile_mapping:
                continue

            pile, created = models.Pile.objects.get_or_create(
                name=pile_mapping[pile_suffix].title())
            if created:
                print >> self.logfile, u'  New Pile:', pile.name

            res = models.Character.objects.filter(short_name=short_name)
            if len(res) == 0:
                print >> self.logfile, u'      MISSING CHARACTER:', short_name
                continue
            character = res[0]

            res = models.CharacterValue.objects.filter(
                value_str=row['character_value'])
            if len(res) == 0:
                cv = models.CharacterValue(value_str=row['character_value'],
                                           character=character)
                cv.save()
            else:
                cv = res[0]

            if not 'friendly_text' in row:
                continue

            friendly_text = row['friendly_text']
            if friendly_text and friendly_text != row['character_value']:
                term, created = models.GlossaryTerm.objects.get_or_create(
                    term=row['character_value'],
                    lay_definition=friendly_text)
                if created:
                    print >> self.logfile, \
                        u'      New Definition: ' + friendly_text
                cv.glossary_term = term

            pile.character_values.add(cv)
            pile.save()

    def _import_character_glossary(self, f):
        print >> self.logfile, 'Setting up character glossary'
        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = {}
            for pos, c in enumerate(cols):
                row[colnames[pos]] = c

            ch = row['character'].split('_')
            pile_suffix = ch[-1]
            ch_short_name = '_'.join(ch[:-1])
            ch_name = ' '.join(ch[:-1])

            if not row['friendly_text']:
                continue
            # only handling the two _ly and _ca piles for now
            if not pile_suffix in pile_mapping:
                continue

            # XXX for now assume char was already created by _import_char.
            # We don't have character_group in current data file.
            char = models.Character.objects.get(short_name=ch_short_name)
            pile,ignore = models.Pile.objects.get_or_create(name=pile_mapping[pile_suffix])
            term, created = models.GlossaryTerm.objects.get_or_create(term=ch_name,
                                                                      question_text=row['friendly_text'],
                                                                      hint=row['hint'],
                                                                      visible=False)

            models.GlossaryTermForPileCharacter.objects.get_or_create(character=char,
                                                                      pile=pile,
                                                                      glossary_term=term)

    def _import_glossary(self, f, imagef):
        print >> self.logfile, 'Setting up glossary'

        # XXX: Assume the default pile for now
        default_pile = models.Pile.objects.all()[0]

        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]
        images = tarfile.open(imagef)

        for cols in iterator:
            row = {}
            for pos, c in enumerate(cols):
                row[colnames[pos]] = c

            if not row['definition'] or row['definition'] == row['term']:
                continue
            # For now we assume term titles are unique
            # SK: this is now a problem, we don't have unique terms anymore
            term, created = models.GlossaryTerm.objects.get_or_create(
                term=row['term'], lay_definition=row['definition'])
            # for new entries add the definition
            if created:
                print >> self.logfile, u'  New glossary term: ' + term.term
            else:
                print >> self.logfile, u'  Updated glossary term: ' + term.term
            try:
                image = images.getmember(row['illustration'])
                image_file = File(images.extractfile(image.name))
                term.image.save(image.name, image_file)
            except KeyError:
                print >> self.logfile, '    No image found for term'

            term.save()

            # search for matching character values
            cvs = models.CharacterValue.objects.filter(
                value_str__iexact=term.term)
            for cv in cvs:
                if not cv.glossary_term:
                    cv.glossary_term = term
                    cv.save()
                    print >> self.logfile, u'   Term %s mapped to character ' \
                          'value: %s' % (term.term, repr(cv))

            # For those that didn't match, we search for matching
            # botanic characters by short_name
            if not cvs:
                chars = models.Character.objects.filter(
                    short_name__iexact=term.term.replace(' ', '_'))
                for char in chars:
                    gpc, created = models.GlossaryTermForPileCharacter.objects.get_or_create(
                            character=char,
                            pile=default_pile,
                            glossary_term=term)
                    print >> self.logfile, u'   Term %s mapped to ' \
                          'character: %s' % (term.term, repr(char))

    def import_species_images(self, dirpath, image_categories_csv):
        """Given a directory's ``dirpath``, find species images inside."""

        # Right now, the image categories CSV is simply used to confirm
        # that we recognize the type of every image we import.

        iterator = iter(CSVReader(image_categories_csv).read())
        colnames = [x.lower() for x in iterator.next()]

        # This dictionary will map (pile_name, type) to description
        taxon_image_types = {}
        for cols in iterator:
            row = dict(zip(colnames, cols))
            # lower() is important because case is often mismatched
            # between the official name of a pile and its name here
            key = (row['pile'].lower(), row['code'])
            # The category looks like "bark, ba" so we split on the comma
            taxon_image_types[key] = row['category'].rsplit(',', 1)[0]

        # We scan the image directory recursively, allowing images to be
        # stored in as deep a directory as they wish.

        ContentImage_objects = models.ContentImage.objects
        print >> self.logfile, 'Searching for images in:', dirpath

        for (subdir, dirnames, filenames) in os.walk(dirpath):

            # Ignore hidden directories

            for i, dirname in reversed(list(enumerate(dirnames))):
                if dirname.startswith('.'):
                    del dirnames[i]

            # Process the filenames.

            for filename in filenames:

                if filename.startswith('.'):  # skip hidden files
                    continue

                if '.' not in filename:  # skip files without an extension
                    continue

                name, ext = filename.split('.')
                if ext.lower() not in ('jpg', 'gif', 'png', 'tif'):
                    continue  # not an image

                # Some images either lack a rank in their name, or
                # supply a letter - which apparently only functions to
                # make unique a sequence of images taken by the same
                # photographer of a particular species.  For all such
                # photos, we assign the first one rank=1, and all
                # subsequent ones rank=2, and issue a warning.

                pieces = name.split('-')
                genus = pieces[0]
                species = pieces[1]

                # Skip subspecies and variety, if provided, and skip
                # ahead to the type field, that always has length 2.

                type_field = 2
                while len(pieces[type_field]) != 2:
                    type_field += 1

                _type = pieces[type_field]
                photographer = pieces[type_field + 1]
                if len(pieces) > (type_field + 2) \
                        and pieces[type_field + 2].isdigit():
                    rank = int(pieces[4])
                else:
                    rank = None

                scientific_name = ' '.join((genus, species)).capitalize()

                # Find the Taxon corresponding to this species.
                try:
                    taxon = models.Taxon.objects.get(
                        scientific_name=scientific_name)
                except ObjectDoesNotExist:
                    # Test whether the "subspecies" field that we
                    # skipped was, in fact, the second half of a
                    # hyphenated species name, like the species named
                    # "Carex merritt-fernaldii".
                    scientific_name = scientific_name + '-' + pieces[2]
                    try:
                        taxon = models.Taxon.objects.get(
                            scientific_name=scientific_name)
                    except:
                        print >> self.logfile, (
                            '  !IMAGE %r NAMES UNKNOWN TAXON' % filename)
                        continue

                content_type = ContentType.objects.get_for_model(taxon)

                # Get the image type, now that we know what pile the
                # species belongs in (PROBLEM: it could be in several;
                # will email Sid about this).  For why we use lower(),
                # see the comment above.

                for pile in taxon.piles.all():
                    key = (pile.name.lower(), _type)
                    if key in taxon_image_types:
                        break
                else:
                    print >> self.logfile, '  !UNKNOWN IMAGE TYPE %r:' % (
                        _type), filename
                    continue

                image_type, created = models.ImageType.objects \
                    .get_or_create(name=taxon_image_types[key])

                # If no rank was supplied, arbitrarily promote the first
                # such image to Rank 1 for its species and type.

                if rank is None:
                    already_1 = ContentImage_objects.filter(
                        rank=1,
                        image_type=image_type,
                        content_type=content_type,
                        object_id=taxon.pk,
                        )
                    if already_1:
                        rank = 2
                    else:
                        print >> self.logfile, '  !WARNING -', \
                            'promoting image to rank=1:', filename
                        rank = 1

                # if we have already imported this image, update the
                # image just in case
                image_path = os.path.join(subdir, filename)
                content_image, created = ContentImage_objects.get_or_create(
                    # If we were simply creating the object we could set
                    # content_object, but in case Django does a "get" we
                    # need to use content_type and object_id instead.
                    object_id=taxon.pk,
                    content_type=content_type,
                    # Use filename to know if this is the "same" image.
                    image=os.path.relpath(image_path, settings.MEDIA_ROOT),
                    defaults=dict(
                        # Integrity errors are triggered without setting
                        # these immediately during a create:
                        rank=rank,
                        image_type=image_type,
                        )
                    )
                content_image.creator = photographer
                content_image.alt = '%s: %s %s' % (
                    taxon.scientific_name, image_type.name, rank)

                msg = 'taxon image %s' % content_image.image
                if created:
                    content_image.save()
                    print >> self.logfile, '  Added', msg
                else:
                    # Update values otherwise set in defaults={} on create.
                    content_image.rank = rank
                    content_image.image_type = image_type
                    content_image.save()
                    print >> self.logfile, '  Updated', msg

    def _import_default_filters(self):
        print >> self.logfile, 'Setting up some default filters'
        pile = models.Pile.objects.get(name='Lycophytes')

        character = models.Character.objects.get(
            short_name='horizontal_shoot_position')
        filter, created = models.DefaultFilter.objects.get_or_create(
            pile=pile,
            character=character,
            order=1,
            key_characteristics=u'1 ugh erg guah',
            notable_exceptions=u'1 foo bar')
        filter.save()

        character = models.Character.objects.get(short_name='spore_form')
        filter, created = models.DefaultFilter.objects.get_or_create(
            pile=pile,
            character=character,
            order=2,
            key_characteristics=u'2 ugh erg guah',
            notable_exceptions=u'2 foo bar')

        filter.save()

        character = models.Character.objects.get(short_name='strobilus_base')
        filter, created = models.DefaultFilter.objects.get_or_create(
            pile=pile,
            character=character,
            order=3,
            key_characteristics=u'3 ugh erg guah',
            notable_exceptions=u'3 foo bar')

        filter.save()

    def _import_plant_preview_characters(self):
        print >> self.logfile, ('Setting up sample plant preview characters')

        pile = models.Pile.objects.get(name='Lycophytes')

        character = models.Character.objects.get(
            short_name='horizontal_shoot_position')
        preview_character, created = \
            models.PlantPreviewCharacter.objects.get_or_create(pile=pile,
                character=character, order=1)
        preview_character.save()

        character = models.Character.objects.get(short_name='spore_form')
        preview_character, created = \
            models.PlantPreviewCharacter.objects.get_or_create(pile=pile,
                character=character, order=2)
        preview_character.save()

        pile = models.Pile.objects.get(name='Non-Orchid Monocots')

        character = models.Character.objects.get(short_name='anther_length')
        preview_character, created = \
            models.PlantPreviewCharacter.objects.get_or_create(pile=pile,
                character=character, order=1)
        preview_character.save()

        character = models.Character.objects.get(
            short_name='leaf_arrangement')
        preview_character, created = \
            models.PlantPreviewCharacter.objects.get_or_create(pile=pile,
                character=character, order=2)
        preview_character.save()

    def _import_extra_demo_data(self):
        print >> self.logfile, 'Setting up demo Pile attributes'
        pile = models.Pile.objects.get(name='Woody Angiosperms')
        if not pile.youtube_id:
            pile.youtube_id = 'LQ-jv8g1YVI'
        if not pile.key_characteristics:
            pile.key_characteristics = '<ul><li>A key characteristic</li><li>Another one</li></ul>'
        if not pile.notable_exceptions:
            pile.notable_exceptions = '<ul><li>An Exception</li><li>Another one</li></ul>'
        if not pile.description:
            pile.description = 'A description of the Woody Angiosperms pile'
        pile.save()

        pile = models.PileGroup.objects.get(name='Woody Plants')
        if not pile.youtube_id:
            pile.youtube_id = 'VWDc9oyBj5Q'
        if not pile.key_characteristics:
            pile.key_characteristics = '<ul><li>A key characteristic</li><li>Another one</li></ul>'
        if not pile.notable_exceptions:
            pile.notable_exceptions = '<ul><li>An Exception</li><li>Another one</li></ul>'
        if not pile.description:
            pile.description = 'A description of the Woody Plants pile group'
        pile.save()


def main():
    # Incredibly lame option parsing, since we can't rely on real option parsing
    if sys.argv[1] == 'species-images':
        species_image_dir = os.path.join(settings.MEDIA_ROOT, 'species')
        Importer().import_species_images(species_image_dir, *sys.argv[2:])
    else:
        Importer().import_data(*sys.argv[1:])


if __name__ == '__main__':
    main()

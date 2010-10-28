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
from gobotany.simplekey.models import Blurb, Video, HelpPage, \
                                      GlossaryHelpPage

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
    'wa': u'Woody Angiosperms',
    'wg': u'Woody Gymnosperms',
    }

class Importer(object):

    def __init__(self, logfile=sys.stdout):
        self.logfile = logfile

    def import_data(self, pilegroupf, pilef, pile_images, taxaf, charf,
                    charvf, char_glossaryf, glossaryf, glossary_images,
                    lookalikesf, *taxonfiles):
        self._import_pile_groups(pilegroupf)
        self._import_piles(pilef, pile_images)
        self._import_taxa(taxaf)
        self._import_characters(charf)
        self._import_character_values(charvf)
        self._import_character_glossary(char_glossaryf)
        self._import_glossary(glossaryf, glossary_images)
        self._import_default_filters()
        self._import_plant_preview_characters()
        self._import_lookalikes(lookalikesf)
        self._import_extra_demo_data()
        self._import_help()
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

    def _import_pile_groups(self, pilegroupf):
        print >> self.logfile, 'Setting up pile groups'
        iterator = iter(CSVReader(pilegroupf).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            pilegroup, created = models.PileGroup.objects.get_or_create(
                name=row['name'],
                friendly_name=row['friendly_name'],
                key_characteristics=row['key_characteristics'],
                notable_exceptions=row['notable_exceptions'])
            if created:
                print >> self.logfile, u'  New PileGroup:', pilegroup

    def _import_piles(self, pilef, pile_images):
        print >> self.logfile, 'Setting up piles'
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
                if created:
                    print >> self.logfile, u'  New PileGroup:', pilegroup
                if pile_images:
                    self._add_pile_images(pilegroup, pile_images, pile_prefixes)

            # Create the Pile.
            pile, created = models.Pile.objects.get_or_create(
                name=row['name'].title())
            pile.pilegroup = pilegroup
            # Update various fields.
            pile.friendly_name = row['friendly_name']
            pile.description = row['description']
            pile.key_characteristics = row['key_characteristics']
            pile.notable_exceptions = row['notable_exceptions']
            pile.save()
            if pile_images:
                self._add_pile_images(pile, pile_images, pile_prefixes)
            if created:
                print >> self.logfile, u'    New Pile:', pile
            else:
                print >> self.logfile, u'    Updated Pile:', pile

    def _import_taxa(self, taxaf):
        print >> self.logfile, 'Setting up taxa in file: %s' % taxaf
        iterator = iter(CSVReader(taxaf).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            # Find the family and genus.
            family, created = models.Family.objects.get_or_create(
                name=row['family'])
            # Uncomment the following statement to diagnose integrity errors.
            #print >> self.logfile, u'TEMP: about to get or create genus: ' \
            #    'row[\'scientific_name\']=%s row[\'family\']=%s' % \
            #    (row['scientific_name'], row['family'])
            genus, created = models.Genus.objects.get_or_create(
                name=row['scientific_name'].split()[0],
                family=family)

            # Create a Taxon.
            taxon = models.Taxon(
                scientific_name=row['scientific_name'],
                family=family,
                genus=genus,
                taxonomic_authority = row['taxonomic_authority'],
                simple_key = (row['simple_key'] == 'TRUE'),
                habitat = row['habitat'],
                factoid = row['factoid'],
                uses = row['uses'],
                wetland_status = row['wetland_status'],
                north_american_native = \
                    (row['native_to_north_america'] == 'TRUE'),
                conservation_status_ct = row['conservation_status_ct'],
                conservation_status_ma = row['conservation_status_ma'],
                conservation_status_me = row['conservation_status_me'],
                conservation_status_nh = row['conservation_status_nh'],
                conservation_status_ri = row['conservation_status_ri'],
                conservation_status_vt = row['conservation_status_vt'],
                distribution = row['distribution'],
                invasive_in_states = row['invasive_in_which_states'],
                sale_prohibited_in_states = \
                    row['prohibited_from_sale_states'],
                )
            taxon.save()
            print >> self.logfile, u'    New Taxon:', taxon

            # Assign this Taxon to the Pile(s) specified for it.
            if row['pile']:
                for pile_name in re.split(r'[,;|]', row['pile']):
                    # Look for a Pile with this name.
                    piles = models.Pile.objects.filter(
                        name__iexact=pile_name.strip())
                    if piles:
                        pile = piles[0]
                        pile.species.add(taxon)
                    else:
                        print >> self.logfile, u'      ERR: cannot find pile:', \
                            pile_name

    def _import_taxon_character_values(self, f):
        print >> self.logfile, 'Setting up taxon character values in file: %s' % f
        iterator = iter(CSVReader(f).read())
        colnames = list(iterator.next())  # do NOT lower(); case is important

        _pile_suffix = colnames[-2][-3:]  # like '_ca'
        pile_suffix = _pile_suffix[1:]   # like 'ca'
        if pile_suffix not in pile_mapping:
            print >> self.logfile, "  ERR: Pile '%s' isn't mapped" % pile_suffix
            return

        pile = models.Pile.objects.get(name__iexact=pile_mapping[pile_suffix])
        print >> self.logfile, '  Setting up taxon character values in ' \
            'pile %s' % pile_mapping[pile_suffix]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            # Look up the taxon and if it exists, import character values.
            taxa = models.Taxon.objects.filter(
                scientific_name__iexact=row['Scientific_Name'])
            if not taxa:
                continue
            taxon = taxa[0]
            
            # Create structure for tracking whether both min & max values have
            # seen for this character, in order to avoid creating unneccessary
            # CharacterValues.
            length_values_seen = {}

            # Go through the key/value pairs for this row.
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
                    print >> self.logfile, '    ERR: No such character ' \
                        'exists: %s, [%s]' % (cname, k)
                    continue

                if is_min or is_max:

                    try:
                        numv = float(v)
                    except ValueError:
                        print >> self.logfile, '    ERR: Can\'t convert to ' \
                            'a number: %s=%s [%s]' % (cname, v, k)
                        continue

                    # Min and max get stored in the same char-value row.
                    tcvs = models.TaxonCharacterValue.objects.filter(
                        taxon=taxon,
                        character_value__character=character,
                        ).all()
                    if tcvs:
                        cv = tcvs[0].character_value
                    else:
                        # If this character hasn't been seen before, make a
                        # place for it.
                        if length_values_seen.has_key(cname) == False:
                            length_values_seen[cname] = {}

                        # Set the min or max value in the temporary data
                        # structure.
                        if is_min:
                            length_values_seen[cname]['min'] = numv
                        else:
                            length_values_seen[cname]['max'] = numv

                        # If we've seen both min and max values for this
                        # character:
                        if length_values_seen[cname].has_key('min') and \
                           length_values_seen[cname].has_key('max'):
                            # Look for an existing character value for this
                            # character and min/max values.
                            cvs = models.CharacterValue.objects.filter(
                                character=character,
                                value_min=length_values_seen[cname]['min'],
                                value_max=length_values_seen[cname]['max'])
                            if cvs:
                                cv = cvs[0]
                            else:
                                # The character value doesn't exist; create.
                                cv = models.CharacterValue(
                                    character=character)
                                cv.value_min = length_values_seen[cname]['min']
                                cv.value_max = length_values_seen[cname]['max']
                                cv.save()
                            # Finally, add the character value.
                            pile.character_values.add(cv)
                            models.TaxonCharacterValue(taxon=taxon,
                                character_value=cv).save()
                            print >> self.logfile, \
                                '  New TaxonCharacterValue: %s, %s for ' \
                                'Character: %s [%s] (Species: %s)' % \
                                (str(cv.value_min), str(cv.value_max),
                                 character.name, cname, taxon.scientific_name)

                else:
                    # A regular comma-separated list of string values.
                    for val in v.split('|'):
                        val = val.strip()
                        # Don't use get_or_created here, otherwise an illegal
                        # CharacterValue could get associated with the taxon.
                        # The universe of possible CharacterValues have already
                        # been constructed in an earlier method.
                        cv = models.CharacterValue.objects.filter(
                            value_str=val,
                            character=character)
                        # Some character values contain commas and shouldn't be 
                        # treated as a comma-seperated list. So let's try
                        # looking it up as single field.
                        if len(cv) == 0:
                            cv = models.CharacterValue.objects.filter(
                                value_str=v,
                                character=character)
                        # Shockingly, if we still get nothing it means the
                        # csv probably contain dirty data, and it's a good
                        # idea to log it.
                        if len(cv) == 0:
                            print >> self.logfile, \
                                '    ERR: No such value: %s for character: ' \
                                '%s [%s] exists' % (val, cname, k)
                            continue

                        models.TaxonCharacterValue.objects.get_or_create(
                            taxon=taxon, character_value=cv[0])
                        print >> self.logfile, \
                            '  New TaxonCharacterValue: %s for Character:' \
                            ' %s [%s] (Species: %s)' % (val, character.name,
                                                        cname,
                                                        taxon.scientific_name)

    def _import_characters(self, f):
        print >> self.logfile, 'Setting up characters in file: %s' % f
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
                unit = row['units']
            else:
                value_type = 'TEXT'

            chargroup, created = models.CharacterGroup.objects.get_or_create(
                name=row['character_group'])
            if created:
                print >> self.logfile, u'    New Character Group:', \
                    chargroup.name

            eoo = row['ease_of_observability']
            eoo = int(eoo)
            
            key_chars = row['key_characteristics']
            notable_ex = row['notable_exceptions']
            
            res = models.Character.objects.filter(short_name=short_name)
            if len(res) == 0:
                print >> self.logfile, u'      New Character: %s (%s)' % \
                    (short_name, value_type)
                # Create a friendly name automatically for now.
                temp_friendly_name = short_name.replace('_', ' ').capitalize()
                character = models.Character(short_name=short_name,
                                             name=temp_friendly_name,
                                             friendly_name=temp_friendly_name,
                                             character_group=chargroup,
                                             value_type=value_type,
                                             unit=unit,
                                             ease_of_observability=eoo,
                                             key_characteristics=key_chars,
                                             notable_exceptions=notable_ex)
                character.save()

    def _import_character_values(self, f):
        print >> self.logfile, 'Setting up character values in file: %s' % f
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
                print >> self.logfile, u'      ERR: missing character: %s' % \
                    short_name
                continue
            character = res[0]
            
            key_chars = row['key_characteristics']
            notable_ex = row['notable_exceptions']

            # note that CharacterValues can be used by multiple Characters
            res = models.CharacterValue.objects.filter(
                value_str=row['character_value'],
                character=character)
            if len(res) == 0:
                cv = models.CharacterValue(value_str=row['character_value'],
                                           character=character,
                                           key_characteristics=key_chars,
                                           notable_exceptions=notable_ex)
                cv.save()
                print >> self.logfile, u'  New Character Value: %s ' \
                    'for Character: %s [%s]' % (cv.value_str, character.name,
                                                row['character'])
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
                print >> self.logfile, '    ERR: No image found for term'

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
                            '  ERR: image %r names unknown taxon' % filename)
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
                    print >> self.logfile, '  ERR: unknown image type %r:' % (
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

                # Force generation of the thumbnails that will be used
                # by (at least) the Simple Key application.
                content_image.image.thumbnail.width()
                content_image.image.extra_thumbnails['large'].width()

    def _create_default_filters(self, pile_name, character_short_names):
        print >> self.logfile, '    Set up default filters for %s' % pile_name
        pile = models.Pile.objects.get(name=pile_name)
        for index, short_name in enumerate(character_short_names):
            character = models.Character.objects.get(short_name=short_name)
            filter, created = models.DefaultFilter.objects.get_or_create(
                pile=pile, character=character, order=index + 1)
            filter.save()

    def _import_default_filters(self):
        print >> self.logfile, 'Setting up some default filters'
        
        # Set up default filters here until there's a way to do so in Access
        # or the Django Admin.
        self._create_default_filters('Lycophytes',
            ['horizontal_shoot_position', 'spore_form', 'strobilus_base'])
        self._create_default_filters('Monilophytes',
            ['life_stage_present', 'habit', 'leaf_disposition'])
        self._create_default_filters('Equisetaceae',
            ['aerial_stem_dimorphism', 'aerial_stem_color',
             'aerial_stem_height'])
        self._create_default_filters('Woody Gymnosperms',
            ['habit', 'plant_height', 'leaf_form'])
        self._create_default_filters('Woody Angiosperms',
            ['plant_habit', 'plant_height', 'armature'])
        self._create_default_filters('Carex',
            ['rhizomes', 'stem_habit', 'plant_height'])
        self._create_default_filters('Poaceae',
            ['duration', 'plant_height', 'number_of_nodes_on_stem'])
        self._create_default_filters('Remaining Graminoids',
            ['stem_cross-section', 'plant_habit', 'underground_organs'])
        self._create_default_filters('Thalloid Aquatic',
            ['root_presence', 'root_number', 'root_sheath_winged'])
        self._create_default_filters('Orchid Monocots',
            ['habit', 'roots', 'underground_organs'])
        self._create_default_filters('Non-Orchid Monocots',
            ['habit', 'roots', 'laticifers'])
        self._create_default_filters('Composites',
            ['habit', 'duration', 'underground_organs'])
        self._create_default_filters('Non-Thalloid Aquatic',
            ['habit', 'roots', 'laticifers'])
        self._create_default_filters('Remaining Non-Monocots',
            ['plant_habit', 'duration', 'plant_life_form'])

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

        character = models.Character.objects.get(short_name='trophophyll_length')
        preview_character, created = \
            models.PlantPreviewCharacter.objects.get_or_create(pile=pile,
                character=character, order=3)
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


    def _import_lookalikes(self, lookalikesf):
        print >> self.logfile, 'Importing look-alike plants.'
        iterator = iter(CSVReader(lookalikesf).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            lookalike, created = models.Lookalike.objects.get_or_create(
                scientific_name=row['taxon'],
                lookalike_scientific_name=row['lookalike_taxon'],
                lookalike_characteristic=row['how_to_tell'])
            if created:
                print >> self.logfile, u'  New Lookalike:', lookalike


    def _set_youtube_id(self, name, youtube_id, pilegroup=False):
        if pilegroup:
            p = models.PileGroup.objects.get(name=name)
        else:
            p = models.Pile.objects.get(name=name)
        if not p.youtube_id:
            p.youtube_id = youtube_id
        p.save()


    def _import_extra_demo_data(self):
        print >> self.logfile, 'Setting up demo Pile attributes'
        pile = models.Pile.objects.get(name='Woody Angiosperms')
        if not pile.key_characteristics:
            pile.key_characteristics = '<ul><li>A key characteristic</li><li>Another one</li></ul>'
        if not pile.notable_exceptions:
            pile.notable_exceptions = '<ul><li>An Exception</li><li>Another one</li></ul>'
        if not pile.description:
            pile.description = 'A description of the Woody Angiosperms pile'
        pile.save()

        pile = models.PileGroup.objects.get(name='Woody Plants')
        if not pile.key_characteristics:
            pile.key_characteristics = '<ul><li>A key characteristic</li><li>Another one</li></ul>'
        if not pile.notable_exceptions:
            pile.notable_exceptions = '<ul><li>An Exception</li><li>Another one</li></ul>'
        if not pile.description:
            pile.description = 'A description of the Woody Plants pile group'
        pile.save()

        # Set up YouTube videos for all pile groups and piles.
        TEMP_VIDEO_ID1 = 'LQ-jv8g1YVI'
        TEMP_VIDEO_ID2 = 'VWDc9oyBj5Q'
        self._set_youtube_id('Ferns', TEMP_VIDEO_ID1, pilegroup=True)
        self._set_youtube_id('Woody Plants', TEMP_VIDEO_ID2, pilegroup=True)
        self._set_youtube_id('Aquatic Plants', TEMP_VIDEO_ID1, pilegroup=True)
        self._set_youtube_id('Graminoids', TEMP_VIDEO_ID2, pilegroup=True)
        self._set_youtube_id('Monocots', TEMP_VIDEO_ID1, pilegroup=True)
        self._set_youtube_id('Non-Monocots', TEMP_VIDEO_ID2, pilegroup=True)
        self._set_youtube_id('Equisetaceae', TEMP_VIDEO_ID2)
        self._set_youtube_id('Lycophytes', TEMP_VIDEO_ID1)
        self._set_youtube_id('Monilophytes', TEMP_VIDEO_ID2)
        self._set_youtube_id('Woody Angiosperms', TEMP_VIDEO_ID1)
        self._set_youtube_id('Woody Gymnosperms', TEMP_VIDEO_ID2)
        self._set_youtube_id('Non-Thalloid Aquatic', TEMP_VIDEO_ID1)
        self._set_youtube_id('Thalloid Aquatic', TEMP_VIDEO_ID2)
        self._set_youtube_id('Carex', TEMP_VIDEO_ID1)
        self._set_youtube_id('Poaceae', TEMP_VIDEO_ID2)
        self._set_youtube_id('Remaining Graminoids', TEMP_VIDEO_ID1)
        self._set_youtube_id('Non-Orchid Monocots', TEMP_VIDEO_ID2)
        self._set_youtube_id('Orchid Monocots', TEMP_VIDEO_ID1)
        self._set_youtube_id('Composites', TEMP_VIDEO_ID2)
        self._set_youtube_id('Remaining Non-Monocots', TEMP_VIDEO_ID1)


    def _create_about_gobotany_page(self):
        help_page, created = HelpPage.objects.get_or_create(
            title='About Go-Botany', url_path='/simple/help/')
        if created:
            print >> self.logfile, u'  New Help page: ', help_page

        NUM_SECTIONS = 3
        for i in range(1, NUM_SECTIONS + 1):
            section = 'section %d' % i

            blurb, created = Blurb.objects.get_or_create(
                name=section + ' heading',
                text='this is the ' + section + ' heading text')
            help_page.blurbs.add(blurb)

            blurb, created = Blurb.objects.get_or_create(
                name=section + ' content',
                text='this is the ' + section + ' content')
            help_page.blurbs.add(blurb)

        help_page.save()


    def _create_getting_started_page(self):
        help_page, created = HelpPage.objects.get_or_create(
            title='Getting Started', url_path='/simple/help/start/')
        if created:
            print >> self.logfile, u'  New Help page: ', help_page

        blurb, created = Blurb.objects.get_or_create(
            name='getting_started',
            text='this is the blurb called getting_started')
        help_page.blurbs.add(blurb)

        TEMP_VIDEO_ID = 'LQ-jv8g1YVI'
        blurb, created = Blurb.objects.get_or_create(
            name='getting_started_youtube_id',
            text=TEMP_VIDEO_ID)
        help_page.blurbs.add(blurb)

        help_page.save()


    def _get_pile_and_group_videos(self, starting_order):
        videos = []
        order = starting_order

        # Note: Would rather have created pile and pile group videos in the
        # order in which they are presented to the user on the initial pages
        # of the Simple Key (as done in the help_collections view and
        # template). But, the data for the initial pages is currently loaded
        # via fixture after the importer finishes, so it's not available here.
        pile_groups = models.PileGroup.objects.all()
        for pile_group in pile_groups:
            if len(pile_group.youtube_id) > 0:
                print >> self.logfile, \
                    u'    Pile group: %s - YouTube video id: %s' % \
                    (pile_group.name, pile_group.youtube_id)
                video, created = Video.objects.get_or_create(
                    title=pile_group.name,
                    youtube_id=pile_group.youtube_id)
                if video:
                    videos.append(video)
                    order = order + 1
            for pile in pile_group.piles.all():
                if len(pile.youtube_id) > 0:
                    print >> self.logfile, \
                        u'      Pile: %s - YouTube video id: %s' % \
                        (pile.name, pile.youtube_id)
                    video, created = Video.objects.get_or_create(
                        title=pile.name,
                        youtube_id=pile.youtube_id)
                    if video:
                        videos.append(video)
                        order = order + 1
        return videos


    def _create_understanding_plant_collections_page(self):
        help_page, created = HelpPage.objects.get_or_create(
            title='Understanding Plant Collections',
            url_path='/simple/help/collections/')
        if created:
            print >> self.logfile, u'  New Help page: ', help_page

        # Add videos associated with each pile group and pile.
        starting_order = 1
        videos = self._get_pile_and_group_videos(starting_order)
        for video in videos:
            help_page.videos.add(video)

        help_page.save()


    def _create_video_help_topics_page(self):
        help_page, created = HelpPage.objects.get_or_create(
            title='Video Help Topics', url_path='/simple/help/video/')
        if created:
            print >> self.logfile, u'  New Help page: ', help_page

        # Add Getting Started video.
        TEMP_VIDEO_ID = 'LQ-jv8g1YVI'
        order = 1
        video, created = Video.objects.get_or_create(
            title='Getting Started', youtube_id=TEMP_VIDEO_ID)
        if video:
            help_page.videos.add(video)

        # Add pile group and pile videos.
        starting_order = order + 1
        videos = self._get_pile_and_group_videos(starting_order)
        for video in videos:
            help_page.videos.add(video)

        help_page.save()


    def _create_glossary_pages(self):
        LETTERS = ('a b c d e f g h i j k l m n o p q r s t u v w x '
                   'y z').split(' ')
        for letter in LETTERS:
            glossary = models.GlossaryTerm.objects.filter(visible=True).extra(
                select={'lower_term': 'lower(term)'}).order_by('lower_term')
            # Skip any glossary terms that start with a number, and filter to
            # the desired letter.
            glossary = glossary.filter(term__gte='a', term__startswith=letter)
            # If terms exist for the letter, create a help page record.
            if len(glossary) > 0:
                help_page, created = GlossaryHelpPage.objects.get_or_create(
                    title='Glossary: ' + letter.upper(),
                    url_path='/simple/help/glossary/' + letter + '/',
                    letter=letter)
                if created:
                    print >> self.logfile, u'  New Glossary Help page: ', \
                        help_page
                # Assign all the terms to the help page.
                for term in glossary:
                    help_page.terms.add(term)
                help_page.save()


    def _import_help(self):
        print >> self.logfile, 'Setting up help pages and content'

        # Create Help page model records to be used for search engine indexing
        # and ideally also by the page templates.
        self._create_about_gobotany_page()
        self._create_getting_started_page()
        self._create_understanding_plant_collections_page()
        self._create_video_help_topics_page()
        self._create_glossary_pages()


def main():
    # Incredibly lame option parsing, since we can't rely on real option parsing
    if sys.argv[1] == 'species-images':
        species_image_dir = os.path.join(settings.MEDIA_ROOT, 'species')
        Importer().import_species_images(species_image_dir, *sys.argv[2:])
    else:
        Importer().import_data(*sys.argv[1:])


if __name__ == '__main__':
    main()

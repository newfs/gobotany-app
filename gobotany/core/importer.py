from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from gobotany import settings
management.setup_environ(settings)

import csv
import sys
import tarfile
import re
from gobotany.core import models
from django.contrib.contenttypes.models import ContentType

TAXON_IMAGE_TYPES = {
    'ha': 'habit',
    'tr': 'vegetative leaves (trophophyll)',
    'sh': 'shoots',
    'br': 'branches',
    'sc': 'spore cones',
    'sp': 'spores',
    }


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

pile_mapping = {'ly': u'Lycophytes', 'ca': u'Carex'}


class Importer(object):

    def __init__(self, logfile=sys.stdout):
        self.logfile = logfile

    def import_data(self, charf, char_glossaryf, glossaryf, glossary_images,
                    pilef, taxaf, pile_images, *taxonfiles):
        self._import_characters(charf)
        self._import_character_glossary(char_glossaryf)
        self._import_glossary(glossaryf, glossary_images)
        self._import_piles(pilef, pile_images)
        self._import_default_filters()
        self._import_extra_demo_data()
        self._import_taxa(taxaf)
        for taxonf in taxonfiles:
            self._import_taxon_character_values(taxonf)

    def _add_pile_images(self, pile, images, prefix_mapping):
        """Adds images for a pile or pile group"""
        # Create the two image types relevant for piles
        filter_image, created = models.ImageType.objects.get_or_create(
            name='filter drawing')
        pile_image, created = models.ImageType.objects.get_or_create(
            name='pile image')

        found_rank_one = False
        for filename in prefix_mapping.get(
            pile.name.lower().replace('-',' ').replace('(','').replace(')',''),
            ()):
            parts = filename.split('-')
            image_type = (parts[-2] == 'filter' and filter_image or
                          pile_image)
            # XXX: arbitrarily set a default image
            if image_type == pile_image and not found_rank_one:
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
                self._add_pile_images(pilegroup, pile_images, pile_prefixes)

            # Create the Pile.
            pile, created = models.Pile.objects.get_or_create(
                name=row['name'].title())
            pile.pilegroup = pilegroup
            # Update the friendly name and description.
            pile.friendly_name = row['friendly_name']
            pile.description = row['description']
            pile.save()
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

            # Create a Taxon if it doesn't exist yet.
            taxon, created = models.Taxon.objects.get_or_create(
                scientific_name=row['scientific_name'])
            # Update taxonomic authority and simple key.
            taxon.taxonomic_authority = row['taxonomic_authority']
            taxon.simple_key = (row['simple_key'] == 'TRUE')
            taxon.save()
            if created:
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
        colnames = [x.lower() for x in iterator.next()]

        pile_suffix = colnames[4][-2:]
        if pile_suffix not in pile_mapping:
            print >> self.logfile, "Pile '%s' isn't mapped" % pile_suffix
            return
        default_pile = models.Pile.objects.get(
            name__iexact=pile_mapping[pile_suffix])

        for cols in iterator:
            row = {}
            for pos, c in enumerate(cols):
                row[colnames[pos]] = c

            # Look up the taxon and if it exists, import character values.
            taxa = models.Taxon.objects.filter(
                scientific_name__iexact=row['scientific_name'])
            if not taxa:
                continue
            t = taxa[0]

            for k, v in row.items():
                if not v.strip():
                    continue
                cname = '_'.join(k.split('_')[:-1])

                is_min = False
                is_max = False
                if cname.endswith('_min'):
                    is_min = True
                    cname = cname[:-4]
                if cname.endswith('_max'):
                    is_max = True
                    cname = cname[:-4]

                try:
                    char = models.Character.objects.get(short_name=cname)
                    # Set the value type here
                except ObjectDoesNotExist:
                    print >> self.logfile, 'No such character exists: %s'%cname
                    continue
                if is_min:
                    try:
                        cvs = taxa.character_values.filter(character=char)
                        if len(cvs) == 0:
                            cvs = models.CharacterValue(character=char,
                                                        value_min=int(v))
                            cvs.save()
                            models.TaxonCharacterValue(taxon=t,
                                                     character_value=cvs).save()
                        else:
                            cvs = cvs[0]
                            cvs.value_min = int(v)
                            cvs.save()
                    except ValueError:
                        print >> self.logfile, 'Not an int: %s; %s' % (cname, v)

                elif is_max:
                    cvs = taxa.character_values.filter(character=char)
                    if len(cvs)  == 0:
                        cvs = models.CharacterValue(character=char,
                                                    value_max=int(v))
                        cvs.save()
                        models.TaxonCharacterValue(taxon=t,
                                                   character_value=cvs).save()
                    else:
                        cvs = cvs[0]
                        cvs.value_max = int(v)
                        cvs.save()
                else:
                    for val in v.split(','):
                        val = val.strip()
                        cvs, created = models.CharacterValue.objects.get_or_create(
                            value_str=val,
                            character=char)
                        cvs.save()
                        models.TaxonCharacterValue.objects.get_or_create(
                            taxon=t,
                            character_value=cvs)
            t.save()

    def _import_characters(self, f):
        print >> self.logfile, 'Setting up characters'
        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = {}
            for pos, c in enumerate(cols):
                row[colnames[pos]] = c

            sp = row['character'].split('_')
            pile_suffix = sp[-1]
            short_name = '_'.join(sp[:-1])
            # Detect lengths and set the short_name and value_type properly
            if short_name.endswith('_min') or short_name.endswith('_max'):
                short_name = short_name[:-4]
                value_type = 'LENGTH'
            else:
                value_type = 'TEXT'

            # only handling the two _ly and _ca piles for now
            if not pile_suffix in pile_mapping:
                continue

            pile, created = models.Pile.objects.get_or_create(
                name=pile_mapping[pile_suffix])
            if created:
                print >> self.logfile, u'  New Pile: ' \
                      + pile_mapping[pile_suffix]

            chargroup, created = models.CharacterGroup.objects.get_or_create(
                name=row['type'])
            if created:
                print >> self.logfile, u'    New Character Group: ' \
                      + row['type']

            res = models.Character.objects.filter(short_name=short_name)
            if len(res) == 0:
                print >> self.logfile, u'      New Character: ' + short_name
                # Create a friendly name automatically for now.
                temp_friendly_name = short_name.replace('_', ' ').capitalize()
                character = models.Character(short_name=short_name,
                                             name=temp_friendly_name,
                                             friendly_name=temp_friendly_name,
                                             character_group=chargroup,
                                             value_type=value_type)
                character.save()
            else:
                character = res[0]

            res = models.CharacterValue.objects.filter(value_str=row['desc'])
            if len(res) == 0:
                cv = models.CharacterValue(value_str=row['desc'],
                                           character=character)
                cv.save()
            else:
                cv = res[0]

            if not 'friendly_text' in row:
                continue

            friendly_text = row['friendly_text']
            if friendly_text and friendly_text != row['desc']:
                term, created = models.GlossaryTerm.objects.get_or_create(
                    term=row['desc'],
                    lay_definition=friendly_text)
                if created:
                    print >> self.logfile, u'      New Definition: ' + friendly_text
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

    def import_taxon_images(self, *files):
        for f in files:
            images = tarfile.open(f)
            for image in images:
                # Skip hidden files and metadata
                if image.name.startswith('.'):
                    continue
                image_name, image_ext = image.name.split('.')
                if image_ext.lower() not in ('jpg', 'gif', 'png', 'tif'):
                    # not an image
                    continue
                parts = image_name.split('-')
                rank = int(parts[-1])
                photographer = parts[-2]
                image_type = TAXON_IMAGE_TYPES[parts[-3]]
                scientific_name = ' '.join(parts[:-3])
                # get or create the image type
                image_type, created = models.ImageType.objects.get_or_create(name=image_type)
                try:
                    taxon = models.Taxon.objects.get(
                        scientific_name__istartswith=scientific_name)
                except ObjectDoesNotExist:
                    print >> self.logfile, 'Could not find Taxon object for %s'%scientific_name
                    continue
                # if we have already imported this image, update the
                # image just in case
                content_image, created = models.ContentImage.objects.get_or_create(
                    rank=rank,
                    image_type=image_type,
                    creator=photographer,
                    # If we were simply creating the object we could
                    # set content_object directly, but since we're
                    # using an optional get, we need to use
                    # content_type and object_id
                    object_id=taxon.pk,
                    content_type=ContentType.objects.get_for_model(taxon))
                content_image.alt='%s: %s %s'%(taxon.scientific_name,
                                               image_type.name,
                                               rank)
                image_file = File(images.extractfile(image.name))
                content_image.image.save(image.name, image_file)
                content_image.save()
                msg = 'taxon image %s'%image.name
                if created:
                    print >> self.logfile, 'Added %s'%msg
                else:
                    print >> self.logfile, 'Updated %s'%msg

    def _import_default_filters(self):
        print >> self.logfile, 'Setting up some default filters'
        pile = models.Pile.objects.get(name='Lycophytes')

        character = models.Character.objects.get(
            short_name='horizontal_shoot_position')
        filter, created = models.DefaultFilter.objects.get_or_create(pile=pile,
                                                                     character=character,
                                                                     order=1)
        filter.save()

        character = models.Character.objects.get(short_name='spore_form')
        filter, created = models.DefaultFilter.objects.get_or_create(pile=pile,
                                                                     character=character,
                                                                     order=2)
        filter.save()

        character = models.Character.objects.get(short_name='strobilus_base')
        filter, created = models.DefaultFilter.objects.get_or_create(pile=pile,
                                                                     character=character,
                                                                     order=3)
        filter.save()

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
    if sys.argv[1] == 'images':
        Importer().import_taxon_images(*sys.argv[2:])
    else:
        Importer().import_data(*sys.argv[1:])


if __name__ == '__main__':
    main()

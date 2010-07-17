from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from gobotany import settings
management.setup_environ(settings)

import csv
import sys
import tarfile
from gobotany import models
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
        with open(self.filename) as f:
            r = csv.reader(f, dialect=csv.excel, delimiter=',')
            for row in r:
                yield [c.decode('Windows-1252') for c in row]

pile_mapping = {'ly': u'Lycophytes', 'ca': u'Carex (sedges)'}


class Importer(object):

    def __init__(self, logfile=sys.stdout):
        self.logfile = logfile

    def import_data(self, charf, char_glossaryf, glossaryf, glossary_images, pilef, pile_images, *taxonfiles):
        self._import_characters(charf)
        self._import_character_glossary(char_glossaryf)
        self._import_glossary(glossaryf, glossary_images)
        for taxonf in taxonfiles:
            self._import_taxons(taxonf)
        self._import_piles(pilef, pile_images) # last, so species already exist

    def _add_pile_images(self, pile, images, prefix_mapping):
        """Adds images for a pile or pile group"""
        # Create the two image types relevant for piles
        filter_image, created = models.ImageType.objects.get_or_create(
            name='filter drawing')
        pile_image, created = models.ImageType.objects.get_or_create(
            name='pile image')

        for filename in prefix_mapping.get(
            pile.name.lower().replace('-',' ').replace('(','').replace(')',''),
            ()):
            parts = filename.split('-')
            image_type = (parts[-2] == 'filter' and filter_image or
                          pile_image)
            content_image, created = models.ContentImage.objects.get_or_create(
                rank=2, # can't use file name to determine rank,
                        # because there are sometimes multiple rank 1
                        # files
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

    def _import_piles(self, f, img):
        print >> self.logfile, 'Setting up pile groups and piles'
        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]
        colnums = range(len(colnames))
        pile_images = tarfile.open(img)
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
            row = dict( (colnames[i], cols[i]) for i in colnums )

            pilegroup, created = models.PileGroup.objects.get_or_create(
                name=row['uber-pile'])
            if created:
                print >> self.logfile, u'  New PileGroup:', pilegroup
            self._add_pile_images(pilegroup, pile_images, pile_prefixes)

            pile, created = models.Pile.objects.get_or_create(
                name=row['pile'])
            # Update the friendly text
            pile.friendly_name = row['pile-happy']
            pile.save()
            if created:
                print >> self.logfile, u'    New Pile:', pile

            pilegroup.piles.add(pile)
            self._add_pile_images(pile, pile_images, pile_prefixes)

            if row['second pile']:
                pile2, created = models.Pile.objects.get_or_create(
                    name=row['second pile'])
                if created:
                    print >> self.logfile, u'    New (second) Pile:', pile
            else:
                pile2 = None

            if not row['species']:
                continue  # yes, believe it or not, some rows have no species

            genus_name, species_name = row['species'].split()[:2]
            scientific_name = genus_name + ' ' + species_name
            taxa = models.Taxon.objects.filter(scientific_name=scientific_name)
            if taxa:
                taxon = taxa[0]
                pile.species.add(taxon)
                if pile2 is not None:
                    pile2.species.add(taxon)
            else:
                print >> self.logfile, u'      CANNOT FIND SPECIES:', \
                    scientific_name

    def _import_taxons(self, f):
        print >> self.logfile, 'Setting up taxons (work in progress)'
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

            res = models.Taxon.objects.filter(
                scientific_name=row['scientific_name'])
            if len(res) > 0:
                continue

            # for now, assume everthing is part of the simple_key
            t = models.Taxon(scientific_name=row['scientific_name'],
                             taxonomic_authority=row['taxonomic_authority'],
                             simple_key=True)
            t.save()

            del row['id']
            del row['taxon_id']
            del row['scientific_name']

            for k, v in row.items():
                if not v.strip():
                    continue
                cname = '_'.join(k.split('_')[:-1])
                try:
                    char = models.Character.objects.filter(short_name=cname)
                except ObjectDoesNotExist:
                    print >> self.logfile, 'No such character exists: %s' \
                          % cname
                    continue
                try:
                    cvs = models.CharacterValue.objects.get(value_str=v,
                                                            character=char)
                except ObjectDoesNotExist:
                    print >> self.logfile, 'No such character value ' \
                          'exists: %s; %s' % (cname, v)
                    continue

                models.TaxonCharacterValue(taxon=t, character_value=cvs).save()
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

            # only handling the two _ly and _ca piles for now
            if not pile_suffix in pile_mapping:
                continue

            res = models.Pile.objects.filter(name=pile_mapping[pile_suffix])
            if len(res) == 0:
                print >> self.logfile, u'  New Pile: ' \
                      + pile_mapping[pile_suffix]
                pile = models.Pile(name=pile_mapping[pile_suffix])
                pile.save()
            else:
                pile = res[0]

            res = models.CharacterGroup.objects.filter(name=row['type'])
            if len(res) == 0:
                print >> self.logfile, u'    New Character Group: ' \
                      + row['type']
                chargroup = models.CharacterGroup(name=row['type'])
                chargroup.save()
            else:
                chargroup = res[0]

            res = models.Character.objects.filter(short_name=short_name)
            if len(res) == 0:
                print >> self.logfile, u'      New Character: ' + short_name
                character = models.Character(short_name=short_name,
                                             character_group=chargroup)
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


def main():
    # Incredibly lame option parsing, since we can't rely on real option parsing
    if sys.argv[1] == 'images':
        Importer().import_taxon_images(*sys.argv[2:])
    else:
        Importer().import_data(*sys.argv[1:])


if __name__ == '__main__':
    main()

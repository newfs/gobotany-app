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

pile_mapping = {'ly': u'Lycophytes', 'ca': u'Carex'}


class Importer(object):

    def import_data(self, charf, glossaryf, glossary_images, *taxonfiles):
        self._import_characters(charf)
        self._import_glossary(glossaryf, glossary_images)
        for taxonf in taxonfiles:
            self._import_taxons(taxonf)

    def _import_taxons(self, f):
        print 'Setting up taxons (work in progress)'
        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]

        pile_suffix = colnames[4][-2:]
        if pile_suffix in pile_mapping:
            default_pile = models.Pile.objects.get(name__iexact=pile_mapping[pile_suffix])

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
                             simple_key=True,
                             pile=default_pile)
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
                    print 'No such character exists: %s' % cname
                    continue
                try:
                    cvs = models.CharacterValue.objects.get(value_str=v,
                                                            character=char)
                except ObjectDoesNotExist:
                    print 'No such character value exists: %s; %s' % (cname, v)
                    continue

                t.character_values.add(cvs)
            t.save()

    def _import_characters(self, f):
        print 'Setting up characters'
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
                print u'  New Pile: ' + pile_mapping[pile_suffix]
                pile = models.Pile(name=pile_mapping[pile_suffix])
                pile.save()
            else:
                pile = res[0]

            res = models.CharacterGroup.objects.filter(name=row['type'])
            if len(res) == 0:
                print u'    New Character Group: ' + row['type']
                chargroup = models.CharacterGroup(name=row['type'])
                chargroup.save()
            else:
                chargroup = res[0]

            res = models.Character.objects.filter(short_name=short_name)
            if len(res) == 0:
                print u'      New Character: ' + short_name
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
            pile.character_values.add(cv)
            pile.save()

    def _import_glossary(self, f, imagef):
        print 'Setting up glossary'

        # XXX: Assume the default pile for now
        default_pile = models.Pile.objects.all()[0]

        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]
        images = tarfile.open(imagef)

        for cols in iterator:
            row = {}
            for pos, c in enumerate(cols):
                row[colnames[pos]] = c

            # For now we assume term titles are unique
            (term,created) = models.GlossaryTerm.objects.get_or_create(
                term=row['term'])
            # for new entries add the definition
            if created:
                term.lay_definition = row['definition']
                print u'  New glossary term: ' + term.term
                try:
                    image = images.getmember(row['illustration'])
                    image_file = File(images.extractfile(image.name))
                    term.image.save(image.name, image_file)
                except KeyError:
                    print '    No image found for term'

                term.save()

            # search for matching character values
            cvs = models.CharacterValue.objects.filter(
                value_str__iexact=term.term)
            for cv in cvs:
                if not cv.glossary_term:
                    cv.glossary_term = term
                    cv.save()
                    print u'   Term %s mapped to character value: %s'%(
                        term.term,
                        repr(cv))

            # For those that didn't match, we search for matching
            # botanic characters by short_name
            if not cvs:
                chars = models.Character.objects.filter(
                    short_name__iexact=term.term.replace(' ', '_'))
                for char in chars:
                    if not char.glossary_terms:
                        gpc = models.GlossaryTermForPileCharacter.objects.create(
                            character=char,
                            pile=default_pile,
                            glossary_term=term)
                        gpc.save()
                        print u'   Term %s mapped to character: %s'%(
                            term.term,
                            repr(char))

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
                    print 'Could not find Taxon object for %s'%scientific_name
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
                    print 'Added %s'%msg
                else:
                    print 'Updated %s'%msg


def main():
    # Incredibly lame option parsing, since we can't rely on real option parsing
    if sys.argv[1] == 'images':
        Importer().import_taxon_images(*sys.argv[2:])
    else:
        Importer().import_data(*sys.argv[1:])


if __name__ == '__main__':
    main()

from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from gobotany import settings
management.setup_environ(settings)

import csv
import sys
from gobotany import models


class CSVReader(object):

    def __init__(self, filename):
        self.filename = filename

    def read(self):
        with open(self.filename) as f:
            r = csv.reader(f, dialect=csv.excel, delimiter=',')
            for row in r:
                yield [c.decode('Windows-1252') for c in row]

pile_mapping = {'ly': u'Lycophytes'}


class Importer(object):

    def import_data(self, charf, taxonf):
        self._import_characters(charf)
        self._import_taxons(taxonf)

    def _import_taxons(self, f):
        print 'Setting up taxons (work in progress)'
        iterator = iter(CSVReader(f).read())
        colnames = [x.lower() for x in iterator.next()]
        default_pile = models.Pile.objects.all()[0]
        for cols in iterator:
            row = {}
            for pos, c in enumerate(cols):
                row[colnames[pos]] = c

            res = models.Taxon.objects.filter(
                scientific_name=row['scientific_name'])
            if len(res) > 0:
                continue

            t = models.Taxon(scientific_name=row['scientific_name'],
                             taxonomic_authority=row['taxonomic_authority'],
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
                    cvs = models.CharacterValue.objects.get(value=v,
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

            # only handling the one _ly pile for now
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

            res = models.CharacterValue.objects.filter(value=row['desc'])
            if len(res) == 0:
                cv = models.CharacterValue(value=row['desc'],
                                           character=character)
                cv.save()
            else:
                cv = res[0]
            pile.character_values.add(cv)
            pile.save()

if __name__ == '__main__':
    Importer().import_data(sys.argv[1], sys.argv[2])

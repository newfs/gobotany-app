import csv
import logging
import os
import re
import shutil
import sys
import tarfile
import xlrd
from collections import defaultdict
from operator import attrgetter
from StringIO import StringIO

# The GoBotany settings have to be imported before most of Django.
from gobotany import settings
from django.core import management
management.setup_environ(settings)

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import connection, transaction
from django.template.defaultfilters import slugify

import bulkup
from gobotany.core import models
from gobotany.simplekey.models import Blurb, Video, HelpPage

DEBUG=False
log = logging.getLogger('gobotany.import')

def start_logging():
    # Log everything to the import.log file.

    logging.basicConfig(filename='import.log', level=logging.DEBUG)

    # Log only INFO and above to the console.

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s  %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def open_csv(filename, lower=True):
    """Our CSVs are produced on Windows and sometimes re-saved from a Mac.

    This means we have to be careful about both their encoding and the
    line endings.  Note that the file must be read as bytes, parsed by
    the CSV module, and then decoded field-by-field; trying to decode
    the file with codecs.open() causes an exception in the csv module.

    """
    w = 'Windows-1252'
    with open(filename, 'r') as f:
        r = csv.reader(f)
        names = [ name.decode(w) for name in r.next() ]
        if lower:
            names = [ name.lower() for name in names ]
        for row in r:
            yield dict(zip(names, (s.decode(w) for s in row)))

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

pile_suffixes = {
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

state_names = {
    'ct': u'Connecticut',
    'ma': u'Massachusetts',
    'me': u'Maine',
    'nh': u'New Hampshire',
    'ri': u'Rhode Island',
    'vt': u'Vermont',
    }


class Importer(object):

    def __init__(self, logfile=sys.stdout):
        self.logfile = logfile

    def character_short_name(self, raw_character_name):
        """Return a short name for a character, to be used in the database."""
        short_name = raw_character_name
        short_name = short_name.replace('_min', '')
        short_name = short_name.replace('_max', '')
        return short_name

    def _import_constants(self, db):
        self._import_plant_preview_characters()
        self._import_extra_demo_data()
        self._import_help()
        self._import_search_suggestions()

    @transaction.commit_on_success
    def _import_partner_sites(self, db):
        log.info('Setting up partner sites')
        partnersite = db.table('core_partnersite')

        for short_name in ['gobotany', 'montshire']:
            partnersite.get(short_name=short_name)

        partnersite.save()

    @transaction.commit_on_success
    def _import_pile_groups(self, db, pilegroupf):
        log.info('Setting up pile groups')
        pilegroup = db.table('core_pilegroup')
        clean = self._clean_up_html

        for row in open_csv(pilegroupf):
            pilegroup.get(
                slug = slugify(row['name']),
                ).set(
                description = '',
                friendly_name = row['friendly_name'],
                friendly_title = row['friendly_title'],
                key_characteristics = clean(row['key_characteristics']),
                name = row['name'].title(),
                notable_exceptions = clean(row['notable_exceptions']),
                youtube_id = '',
                )

        pilegroup.save()

    @transaction.commit_on_success
    def _import_piles(self, db, pilef):
        log.info('Setting up piles')
        pilegroup_map = db.map('core_pilegroup', 'slug', 'id')
        pile = db.table('core_pile')
        clean = self._clean_up_html

        for row in open_csv(pilef):
            if row['name'].lower() in ('all', 'unused'):
                continue

            pile.get(
                slug = slugify(row['name']),
                ).set(
                name = row['name'].title(),
                pilegroup_id = pilegroup_map[slugify(row['pile_group'])],
                friendly_name = row['friendly_name'],
                friendly_title = row['friendly_title'],
                description = row['description'],
                key_characteristics = clean(row['key_characteristics']),
                notable_exceptions = clean(row['notable_exceptions']),
                youtube_id = '',
                )

        pile.save()

    @transaction.commit_on_success
    def _import_habitats(self, db, habitatsf):
        log.info('Setting up habitats')
        habitat = db.table('core_habitat')

        for row in open_csv(habitatsf):
            habitat.get(
                name=row['desc'],
                ).set(
                friendly_name=row['friendly_text'],
                )

        habitat.save()

    def _get_wetland_status(self, status_code):
        '''
        Return plain language text for a wetland status code.
        '''
        status = 'not classified'
        if status_code == 'FAC' or status_code == 'FAC+' or \
           status_code == 'FAC-':
            status = 'Occurs in wetlands or uplands.'
        elif status_code == 'FACU':
            status = ('Usually occurs in uplands, but occasionally occurs '
                      'in wetlands.')
        elif status_code == 'FACU+':
            status = 'Occurs most often in uplands; rarely in wetlands.'
        elif status_code == 'FACU-':
            status = ('Usually occurs in uplands, but occurs in wetlands '
                      'more than occasionally.')
        elif status_code == 'FACW':
            status = ('Usually occurs in wetlands, but occasionally occurs '
                      'in non-wetlands.')
        elif status_code == 'FACW+':
            status = 'Occurs most often in wetlands; rarely in non-wetlands.'
        elif status_code == 'FACW-':
            status = ('Occurs in wetlands but also occurs in uplands more '
                      'than occasionally.')
        elif status_code == 'OBL':
            status = 'Occurs only in wetlands.'
        elif status_code == 'UPL':
            status = 'Never occurs in wetlands.'
        return status


    def _get_state_status(self, state_code, distribution,
                          conservation_status_code=None,
                          is_north_american_native=True, is_invasive=False,
                          is_prohibited=False):
        status = ['absent']

        for state in distribution:
            if state == state_code:
                status = ['present']

                # Most further status information applies only to plants that
                # are present.

                # TODO: remove this code (and the method parameter) once it's
                # confirmed that native status doesn't need to be here.
                #if is_north_american_native == False:
                #    status.append('not native')

                if conservation_status_code == 'E':
                    status.append('endangered')
                elif conservation_status_code == 'T':
                    status.append('threatened')
                elif conservation_status_code == 'SC' or \
                     conservation_status_code == 'SC*':
                    status.append('special concern')
                elif conservation_status_code == 'H':
                    status.append('historic')
                elif conservation_status_code == 'C':
                    status.append('rare')

                if is_invasive == True:
                    status.append('invasive')

        # Extinct status applies to plants that are absent or present.
        # (Present suggests the plant used to be found in the state.)
        if conservation_status_code == 'X':
            # If status is just 'present' or 'absent' so far, clear it so that
            # 'extinct' appears alone.
            if status == ['present'] or status == ['absent']:
                status = []
            status.append('extinct')

        # Prohibited status applies even to plants that are absent.
        if is_prohibited == True:
            status.append('prohibited')

        return ', '.join(status)


    def _get_all_states_status(self, taxon, taxon_data_row):
        DATA_DELIMITER = '|'
        STATES = ['CT', 'MA', 'ME', 'NH', 'RI', 'VT']
        states_status = dict().fromkeys(STATES, '')
    
        distribution = []
        if taxon.distribution:
            distribution = taxon.distribution.replace(' ', '').split( \
                DATA_DELIMITER)

        #is_native = (taxon.north_american_native == True)

        invasive_states = []
        if taxon.invasive_in_states:
            invasive_states = taxon.invasive_in_states.replace( \
                ' ', '').split(DATA_DELIMITER)

        prohibited_states = []
        if taxon.sale_prohibited_in_states:
            prohibited_states = \
                taxon.sale_prohibited_in_states.replace(' ', '').split( \
                    DATA_DELIMITER)

        for state in STATES:
            status_field_name = 'conservation_status_%s' % state.lower()
            conservation_status = taxon_data_row[status_field_name]
            invasive = (state in invasive_states)
            prohibited = (state in prohibited_states)
            states_status[state] = self._get_state_status(state, distribution,
                conservation_status_code=conservation_status,
                is_north_american_native=taxon.north_american_native,
                is_invasive=invasive, is_prohibited=prohibited)

        return states_status


    def _strip_taxonomic_authority(self, full_plant_name):
        """Strip the taxonomic authority out of a full plant name."""
        CONNECTING_TERMS = ['subsp.', 'ssp.', 'var.', 'subvar.', 'f.',
                            'forma', 'subf.']
        UNEXPECTED_CHARACTERS = [u'\N{NO-BREAK SPACE}', u'\N{DAGGER}',
            u'\N{EURO SIGN}', u'\N{LATIN SMALL LETTER A WITH CIRCUMFLEX}']

        # Replace unexpected characters before splitting.
        if not isinstance(full_plant_name, unicode):
            full_plant_name = unicode(full_plant_name, 'UTF-8')
        for character in UNEXPECTED_CHARACTERS:
            full_plant_name = full_plant_name.replace(character, u' ')

        name = []
        words = full_plant_name.split(' ')
        if len(words) > 1:
            # Start with the generic name and specific epithet.
            name.append(words[0])
            name.append(words[1].strip(','))

            # Move through the remaining words, looking for an infraspecific
            # epithet.
            for i in range(2, len(words)):
                if words[i] in CONNECTING_TERMS:
                    next_index = i + 1
                    if len(words) > next_index:
                        if words[next_index] in CONNECTING_TERMS:
                            # If the next word is a connector too, skip ahead.
                            continue
                    # Only append the connector (and the epithet that follows)
                    # if an epithet is actually there, that is, if the string
                    # hasn't ended without one.
                    if len(words) > next_index:
                        name.append(words[i])
                        epithet = words[next_index]
                        # If anything but lowercase letters or a hyphen is
                        # found, chop off the string starting at that point.
                        # This is to handle some cases where a space is
                        # missing after the epithet.
                        match = re.search('[^a-z\-]', epithet)
                        if match:
                            epithet = epithet[:match.start()]
                        name.append(epithet)
                    break
        return ' '.join(name).encode('utf-8')

    @transaction.commit_on_success
    def _import_taxa(self, db, taxaf):
        log.info('Loading taxa from file: %s', taxaf)

        COMMON_NAME_FIELDS = ['common_name1', 'common_name2']
        SYNONYM_FIELDS = ['comment']
        gobotany_id = models.PartnerSite.objects.get(short_name='gobotany').id

        family_table = db.table('core_family')
        genus_table = db.table('core_genus')
        taxon_table = db.table('core_taxon')
        partnerspecies_table = db.table('core_partnerspecies')
        pile_species_table = db.table('core_pile_species')
        commonname_table = db.table('core_commonname')
        synonym_table = db.table('core_synonym')

        pile_map = db.map('core_pile', 'slug', 'id')

        for row in open_csv(taxaf):

            family_slug = slugify(row['family'])
            family_table.get(
                slug=family_slug,
                ).set(
                common_name='',
                description='',
                name=row['family'],
                )

            genus_name = row['scientific__name'].split()[0]
            genus_slug = slugify(genus_name)
            genus_table.get(
                slug=genus_slug,
                ).set(
                common_name='',
                description='',
                family_id=family_slug,
                name=genus_name,
                )

            # Create a Taxon.
            taxon_proxy_id = row['scientific__name']

            taxon = taxon_table.get(
                scientific_name=row['scientific__name'],
                ).set(
                family_id=family_slug,
                genus_id=genus_slug,
                taxonomic_authority=row['taxonomic_authority'],
                habitat=row['habitat'],
                habitat_general='',
                factoid=row['factoid'],
                wetland_status_code=row['wetland_status'],
                wetland_status_text=self._get_wetland_status(
                    row['wetland_status']),
                north_american_native=(
                    row['native_to_north_america_2'] == 'TRUE'),
                distribution=row['distribution'],
                invasive_in_states=row['invasive_in_which_states'],
                sale_prohibited_in_states=row['prohibited_from_sale_states'],
                description='',
                )

            # Assign distribution and conservation status for all states.

            states_status = self._get_all_states_status(taxon, row)
            for state in states_status.keys():
                status_field_name = 'conservation_status_%s' % state.lower()
                setattr(taxon, status_field_name, states_status[state])

            # Assign all imported species to the Go Botany "partner" site.

            partnerspecies_table.get(
                species_id=taxon_proxy_id,
                partner_id=gobotany_id,
                ).set(
                simple_key=(row['simple_key'] == 'TRUE'),
                )

            # Assign this Taxon to the Pile(s) specified for it.

            if row['pile']:
                for pile_name in re.split(r'[,;|]', row['pile']):
                    pile_slug = slugify(pile_name.strip())
                    pile_species_table.get(
                        pile_id=pile_map[pile_slug],
                        taxon_id=taxon_proxy_id,
                        )

            # Add any common names.

            for common_name_field in COMMON_NAME_FIELDS:
                common_name = row[common_name_field].strip()
                if common_name:
                    commonname_table.get(
                        common_name=common_name,
                        taxon_id=taxon_proxy_id,
                        )

            # Add any synonyms.

            for synonym_field in SYNONYM_FIELDS:
                names = [n.strip() for n in row[synonym_field].split(';')]
                for name in names:
                    scientific_name = self._strip_taxonomic_authority(name)
                    # Besides checking to see that the scientific name isn't
                    # empty, also avoid those that look obviously malformed,
                    # as was seen with some bad data.
                    if not scientific_name:
                        continue
                    if scientific_name.startswith(' '):
                        continue
                    synonym_table.get(
                        scientific_name=scientific_name,
                        taxon_id=taxon_proxy_id,
                        ).set(
                        full_name=name,
                        )

        # Write out the tables.

        family_table.save()
        family_map = db.map('core_family', 'slug', 'id')
        genus_table.replace('family_id', family_map)
        genus_table.save()
        genus_map = db.map('core_genus', 'slug', 'id')
        taxon_table.replace('family_id', family_map)
        taxon_table.replace('genus_id', genus_map)
        taxon_table.save()
        taxon_map = db.map('core_taxon', 'scientific_name', 'id')
        partnerspecies_table.replace('species_id', taxon_map)
        partnerspecies_table.save()
        pile_species_table.replace('taxon_id', taxon_map)
        pile_species_table.save(delete_old=True)
        commonname_table.replace('taxon_id', taxon_map)
        commonname_table.save(delete_old=True)
        synonym_table.replace('taxon_id', taxon_map)
        synonym_table.save(delete_old=True)

    # TODO: can we remove this import function and the model PlantNames?
    # It claims to be used by MyPlants but is a completely unindexed table.

    @transaction.commit_on_success
    def _import_plant_names(self, taxaf):
        print >> self.logfile, 'Setting up plant names in file: %s' % taxaf
        COMMON_NAME_FIELDS = ['common_name1', 'common_name2']
        iterator = iter(CSVReader(taxaf).read())
        colnames = [x.lower() for x in iterator.next()]

        for cols in iterator:
            row = dict(zip(colnames, cols))

            scientific_name = row['scientific__name']
            num_common_names = 0
            for common_name_field in COMMON_NAME_FIELDS:
                common_name = row[common_name_field]
                if len(common_name) > 0:
                    num_common_names += 1
                    pn, created = models.PlantName.objects.get_or_create( \
                        scientific_name=scientific_name,
                        common_name=common_name)
                    print >> self.logfile, u'  Added plant name:', pn
            # If there were no common names for this plant, add the plant now.
            if num_common_names == 0:
                pn, created = models.PlantName.objects.get_or_create( \
                    scientific_name=scientific_name)
                print >> self.logfile, u'  Added plant name:', pn

    @transaction.commit_on_success
    def _import_taxon_character_values(self, db, *filenames):

        # Create a pile_map {'_ca': 8, '_nm': 9, ...}
        pile_map1 = db.map('core_pile', 'slug', 'id')
        pile_map = dict(('_' + suffix, pile_map1[slugify(name)])
                        for (suffix, name) in pile_suffixes.iteritems())

        taxon_map = db.map('core_taxon', 'scientific_name', 'id')
        character_map = db.map('core_character', 'short_name', 'id')
        cv_map = db.map(
            'core_charactervalue', ('character_id', 'value_str'), 'id')

        cv_table = db.table('core_charactervalue')
        tcv_table = db.table('core_taxoncharactervalue')

        bad_float_values = set()
        unknown_characters = set()
        unknown_character_values = set()

        for filename in filenames:
            log.info('Loading %s', filename)
            pile_id = None

            # Do *not* lower() column names; case is important!
            for row in open_csv(filename, lower=False):

                # Look up the taxon.
                taxon_id = taxon_map.get(row['Scientific__Name'])
                if taxon_id is None:
                    log.error('Unknown taxon: %r', row['Scientific__Name'])
                    continue

                # Create a structure for tracking whether both min and
                # max values have been seen for this character, in order
                # to avoid creating unnecessary CharacterValues.
                length_pairs = defaultdict(lambda: [None, None])

                # Go through the key/value pairs for this row.
                for character_name, v in row.items():
                    if not v.strip():
                        continue
                    suffix = character_name[-3:]  # '_ca', etc.
                    pile_id = pile_map.get(suffix)
                    if pile_id is None:
                        continue

                    short_name = self.character_short_name(character_name)
                    character_id = character_map.get(short_name)
                    if character_id is None:
                        unknown_characters.add(short_name)
                        continue

                    is_min = '_min' in character_name.lower()
                    is_max = '_max' in character_name.lower()

                    if is_min or is_max:
                        if v == 'n/a':
                            continue
                        try:
                            numv = float(v)
                        except ValueError:
                            bad_float_values.add(v)
                            continue

                        index = 0 if is_min else 1
                        length_pairs[short_name][index] = numv

                    else:
                        # We can create normal tcv rows very simply.

                        for value_str in v.split('|'):
                            value_str = value_str.strip()
                            cvkey = (character_id, value_str)
                            cv_id = cv_map.get(cvkey)
                            if cv_id is None:
                                unknown_character_values.add(cvkey)
                                continue
                            tcv_table.get(
                                taxon_id=taxon_id,
                                character_value_id=cv_id,
                                )

                # Now we have seen both the min and max of every range.

                for character_name, (vmin, vmax) in length_pairs.iteritems():
                    # if vmin is None or vmax is None:  # should we do this?
                    #     continue
                    character_id = character_map[character_name]
                    cv_table.get(
                        character_id=character_id,
                        value_min=vmin,
                        value_max=vmax,
                        ).set(
                        friendly_text='',
                        )
                    tcv_table.get(
                        taxon_id=taxon_id,
                        character_value_id=(character_id, vmin, vmax),
                        )

        for s in sorted(bad_float_values):
            log.debug('Bad floating-point value: %s', s)
        for s in sorted(unknown_characters):
            log.debug('Unknown character: %s', s)
        for s in sorted(unknown_character_values):
            log.debug('Unknown character value: %s', s)

        cv_table.save()

        # Build a composite map so that ids we already have can pass
        # through unscathed, while our triples get dereferenced.
        cv_map = db.map('core_charactervalue', 'id', 'id')
        cv_map2 = db.map('core_charactervalue',
                        ('character_id', 'value_min', 'value_max'),
                        'id')
        cv_map.update(cv_map2)

        tcv_table.replace('character_value_id', cv_map)

        tcv_table.save()

    def _create_character_name(self, short_name):
        """Create a character name from the short name."""
        name = short_name

        # Remove pile suffix, if present.
        if re.search('_[a-z]{2}$', name):
            name = name[:-3]

        name = name.replace('_', ' ').capitalize()
        return name


    def _get_character_friendly_name(self, short_name, friendly_name):
        """Return a laypersons' version of the character name, making one
           from the short name if needed.
        """
        if not friendly_name:
            # Create a character friendly name from the short name.
            friendly_name = self._create_character_name(short_name)
        return friendly_name

    @transaction.commit_on_success
    def _import_characters(self, db, filename):
        log.info('Loading characters from file: %s', filename)
        charactergroup_table = db.table('core_charactergroup')
        character_table = db.table('core_character')

        for row in open_csv(filename):

            if '_' not in row['character']:
                continue # ignore "family" rows for right now

            # Detect length characters and handle accordingly.
            character_name = row['character']
            is_min = '_min' in character_name.lower()
            is_max = '_max' in character_name.lower()
            short_name = self.character_short_name(character_name)

            if is_min or is_max:
                value_type = 'LENGTH'
                unit = row['units']
            else:
                value_type = 'TEXT'
                unit = ''

            charactergroup = charactergroup_table.get(
                name=row['character_group'],
                )

            eoo = row['ease_of_observability']
            try:
                eoo = int(eoo)
            except ValueError:
                log.error('Bad ease-of-observability value: %s', repr(eoo))
                eoo = 10

            question = row['friendly_text']
            hint = row['hint']

            name = self._create_character_name(short_name)
            friendly_name = self._get_character_friendly_name(
                short_name, row['filter_label'])
            character_table.get(
                short_name=short_name,
                ).set(
                name=name,
                friendly_name=friendly_name,
                character_group_id=charactergroup.name,
                value_type=value_type,
                unit=unit,
                ease_of_observability=eoo,
                question=question,
                hint=hint,
                )

        charactergroup_table.save()
        charactergroup_map = db.map('core_charactergroup', 'name', 'id')
        character_table.replace('character_group_id', charactergroup_map)
        character_table.save()

    @transaction.commit_on_success
    def _import_character_images(self, db, csvfilename, tarfilename):
        log.info('Loading character images')
        images = tarfile.open(tarfilename)

        n = 0
        for row in open_csv(csvfilename):
            image_name = row['image_name']
            if not image_name:
                continue
            try:
                image = images.getmember(image_name)
            except KeyError:
                log.error('cannot find image: %s', image_name)
                continue
            image_file = File(images.extractfile(image.name))

            short_name = self.character_short_name(row['character'])
            character = models.Character.objects.get(short_name=short_name)

            character.image.save(image.name, image_file)
            character.image.thumbnail.height()  # generate thumbnail
            n += 1

        log.info('Done loading %s images', n)

    def _clean_up_html(self, html):
        """Clean up HTML ugliness arising from Access rich text export."""

        # Get rid of non-breaking spaces. These are sometimes seen in the data
        # when a sentence ends (after a period and a regular space).
        html = html.replace('&nbsp;', '')

        # Get rid of any <font> tags.
        html = re.sub(r'<\/?font.*?>', '', html)

        return html

    @transaction.commit_on_success
    def _import_character_values(self, db, filename):
        log.info('Loading character values from: %s', filename)
        pile_map = db.map('core_pile', 'name', 'id')
        character_map = db.map('core_character', 'short_name', 'id')
        charactervalue_table = db.table('core_charactervalue')
        pile_character_values_table = db.table('core_pile_character_values')

        for row in open_csv(filename):

            character_name = row['character']
            if character_name == 'family':
                continue
            if '_' not in character_name:
                log.warn('ignoring %r', character_name)
                continue

            pile_suffix = character_name.rsplit('_', 1)[1]
            if not pile_suffix in pile_suffixes:
                continue

            short_name = self.character_short_name(character_name)
            value_str = row['character_value']

            try:
                character_id = character_map[short_name]
            except KeyError:
                log.error('Bad character: %r', short_name)
                continue
            pile_title = pile_suffixes[pile_suffix].title()

            charactervalue_table.get(
                character_id=character_id,
                value_str=value_str,
                ).set(
                friendly_text=self._clean_up_html(row['friendly_text'])
                )

            pile_character_values_table.get(
                pile_id=pile_map[pile_title],
                charactervalue_id=(character_id, value_str),
                )

        charactervalue_table.save()
        charactervalue_map = db.map(
            'core_charactervalue', ('character_id', 'value_str'), 'id')
        pile_character_values_table.replace(
            'charactervalue_id', charactervalue_map)
        pile_character_values_table.save(delete_old=True)

    @transaction.commit_on_success
    def _import_character_value_images(self, db, csvfilename, tarfilename):
        log.info('Loading character value images')
        images = tarfile.open(tarfilename)
        character_map = db.map('core_character', 'short_name', 'id')

        n = 0
        for row in open_csv(csvfilename):

            character_name = row['character']
            if character_name == 'family':
                continue
            if '_' not in character_name:
                log.warn('ignoring %r', character_name)
                continue

            image_name = row['image_name']
            if not image_name:
                continue
            try:
                image = images.getmember(image_name)
            except KeyError:
                log.error('cannot find image: %s', image_name)
                continue
            image_file = File(images.extractfile(image.name))

            # Get character-value, using logic like that above.

            pile_suffix = character_name.rsplit('_', 1)[1]
            if not pile_suffix in pile_suffixes:
                continue

            short_name = self.character_short_name(character_name)
            value_str = row['character_value']

            try:
                character_id = character_map[short_name]
            except KeyError:
                log.error('Bad character: %r', short_name)
                continue

            cv = models.CharacterValue.objects.get(
                character=character_id,
                value_str=value_str,
                )
            cv.image.save(image.name, image_file)
            cv.image.thumbnail.height()  # generate thumbnail
            n += 1

        log.info('Done loading %s images', n)

    @transaction.commit_on_success
    def _import_glossary(self, db, filename):
        log.info('Loading glossary from file: %s', filename)
        glossaryterm_table = db.table('core_glossaryterm')

        for row in open_csv(filename):

            if not row['definition'] or row['definition'] == row['term']:
                continue

            # For now we assume term titles are unique
            # SK: this is now a problem, we don't have unique terms anymore
            glossaryterm_table.get(
                term=row['term'],
                ).set(
                hint='',
                lay_definition=row['definition'],
                question_text='',
                visible=True,
                )

        glossaryterm_table.save()

    @transaction.commit_on_success
    def _import_glossary_images(self, db, csvfilename, tarfilename):
        dirname = models.GlossaryTerm._meta.get_field('image').upload_to
        dirpath = os.path.join(settings.MEDIA_ROOT, dirname)
        log.info('Deleting every file under MEDIA_ROOT/%s' % dirname)

        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)

        # When an archive is compressed, reading all of its members in a
        # single sweep is vastly more efficient than asking for each
        # member separately which makes `tarfile` re-read the compressed
        # archive over and over again.

        log.info('Reading glossary images from archive')
        image_dict = {}
        archive = tarfile.open(tarfilename)
        while True:
            member = archive.next()
            if member is None: break
            data = archive.extractfile(member).read()
            image_dict[member.name] = ContentFile(data)

        log.info('Saving glossary images in MEDIA_ROOT/%s' % dirname)
        for row in open_csv(csvfilename):

            if not row['definition'] or row['definition'] == row['term']:
                continue

            image_name = row['illustration']
            if not image_name:
                continue

            image_file = image_dict.get(row['illustration'])
            if image_file is None:
                log.error('cannot find image: %s', row['illustration'])
                continue

            term = models.GlossaryTerm.objects.get(term=row['term'])
            term.image.save(image_name, image_file)

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

                print >> self.logfile, 'INFO: current image, ', filename

                if filename.startswith('.'):  # skip hidden files
                    continue

                if '.' not in filename:  # skip files without an extension
                    continue

                if filename.count('.') > 1: # skip files w/more than one dot
                    print >> self.logfile, \
                        'ERR: image has multiple periods:', filename
                    continue

                if filename.count('_') > 0: # skip files with underscores
                    print >> self.logfile, \
                        'ERR: image has underscores:', filename
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
                rank = None
                # Filenames no longer contain 'rank' data, so skip this
                # for now.
                # if len(pieces) > (type_field + 2) \
                #         and pieces[type_field + 2].isdigit():
                #     rank = int(pieces[4])
                # else:
                #     rank = None

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
                    print >> self.logfile, \
                        '  ERR: unknown image type %r:' % (_type), filename
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


    def import_home_page_images(self, dest_image_dir_path, images_archive):
        """Import default home page images and put image files in the
        specified directory.
        """
        print >> self.logfile, 'Importing home page images.'
        print >> self.logfile, 'Deleting existing images:'
        for home_page_image in models.HomePageImage.objects.all():
            print >> self.logfile, '  Deleting image %s' % home_page_image
            home_page_image.image.delete()
            home_page_image.delete()

        'Adding images from archive file:'
        images = tarfile.open(images_archive)
        image_names = [name for name in images.getnames()
                       if not name.startswith('.')]
        # The default images are just added in reverse directory order
        # because that was a pretty good sequence without having to
        # code up a way to specify the default order in the archive file.
        image_names.reverse()
        order = 1
        for name in image_names:
            print '  Adding image: %s' % name
            image_file = File(images.extractfile(name))
            hpi, created = models.HomePageImage.objects.get_or_create(
                order=order)
            hpi.image.save(name, image_file)
            order += 1


    def _has_unexpected_delimiter(self, text, unexpected_delimiter):
        """Check for an unexpected delimiter to help guard against breaking
           the app completely silently.
        """
        if text.find(unexpected_delimiter) > -1:
            print >> self.logfile, u'  Error: unexpected delimiter:', \
                unexpected_delimiter
            return True
        else:
            return False


    def _get_friendly_habitat_name(self, habitat_name):
        """For a given habitat name, return the friendly name (if present)."""
        if not habitat_name:
            return None
        friendly_name = None
        try:
            habitat = models.Habitat.objects.get(name__iexact=habitat_name)
            friendly_name = habitat.friendly_name
        except models.Habitat.DoesNotExist:
            print >> self.logfile, u'  Error: habitat does not exist:', \
                habitat_name
        return friendly_name and friendly_name.lower()


    @transaction.commit_on_success
    def _import_places(self, db, taxaf):
        log.info('Setting up place characters and values')

        # Create a character group for "place" characters.

        charactergroup_table = db.table('core_charactergroup')
        charactergroup_table.get(
            name='place',
            )
        charactergroup_table.save()

        charactergroup_map = db.map('core_charactergroup', 'name', 'id')
        charactergroup_id = charactergroup_map['place']

        # Create characters.

        character_table = db.table('core_character')

        characters = [
            ('habitat', 'Specific habitat',
             'What specific kind of habitat is your plant found in?'),
            ('habitat_general', 'Habitat',
             'What kind of habitat is your plant found in?'),
            ('state_distribution', 'New England state',
             'In which New England state did you find the plant?')
            ]
        value_type = 'TEXT'
        for short_name, friendly_name, question in characters:

            character_table.get(
                short_name=short_name,
                ).set(
                name=friendly_name,
                friendly_name=friendly_name,
                character_group_id=charactergroup_id,
                value_type=value_type,
                unit='',
                ease_of_observability=1,
                question=question,
                hint='',
                )

        character_table.save()

        # Go through all of the taxa and create character values.

        character_map = db.map('core_character', 'short_name', 'id')
        taxon_map = db.map('core_taxon', 'scientific_name', 'id')
        pile_map = db.map('core_pile', 'slug', 'id')

        charactervalue_table = db.table('core_charactervalue')
        taxoncharactervalue_table = db.table('core_taxoncharactervalue')
        pile_character_values_table = db.table('core_pile_character_values')

        for row in open_csv(taxaf):

            # Get the taxon and pile (or piles) associated with this row.

            taxon_id = taxon_map[row['scientific__name']]

            pile_names = row['pile'].split('| ')
            pile_ids = [pile_map[slugify(name)] for name in pile_names]

            # We will build a list of values to insert.

            cvfs = []  # (character_id, value_str, friendly_text) tuples

            # Habitat character values.

            character_id = character_map['habitat']
            habitats = row['habitat'].lower().split('| ')
            for habitat in habitats:
                friendly_habitat = self._get_friendly_habitat_name(habitat)
                cvfs.append((character_id, habitat.lower(), friendly_habitat))

            # Habitat (general) chararcter values.

            character_id = character_map['habitat_general']
            habitats = row['habitat_general'].lower().split('| ')
            for habitat in habitats:
                cvfs.append((character_id, habitat, habitat))

            # State Distribution character values.

            character_id = character_map['state_distribution']
            state_codes = row['distribution'].lower().split('| ')
            for state_code in state_codes:
                state = ''
                if state_code in state_names:
                    state = state_names[state_code]
                cvfs.append((character_id, state, ''))

            # Based on the little list we have created, do the inserts!

            for character_id, value_str, friendly_text in cvfs:

                # Don't try to add a value if it's empty.
                if not value_str:
                    continue

                charactervalue_table.get(
                    character_id=character_id,
                    value_str=value_str,
                    ).set(
                    friendly_text=friendly_text,
                    )

                for pile_id in pile_ids:
                    pile_character_values_table.get(
                        pile_id=pile_id,
                        charactervalue_id=(character_id, value_str),
                        )

                taxoncharactervalue_table.get(
                    taxon_id=taxon_id,
                    character_value_id=(character_id, value_str),
                    )

        # Finally, save everything.

        charactervalue_table.save()
        cv_map = db.map(
            'core_charactervalue', ('character_id', 'value_str'), 'id')

        taxoncharactervalue_table.replace('character_value_id', cv_map)
        taxoncharactervalue_table.save()

        pile_character_values_table.replace('charactervalue_id', cv_map)
        pile_character_values_table.save()


    def _create_plant_preview_characters(self, pile_name,
                                         character_short_names,
                                         partner_site_short_name='gobotany'):
        pile = models.Pile.objects.get(name=pile_name)
        partner_site = None
        if partner_site_short_name:
            partner_site = models.PartnerSite.objects.get( \
                short_name=partner_site_short_name)

        for order, short_name in enumerate(character_short_names):
            character = models.Character.objects.get(short_name=short_name)

            preview_character, created = \
                models.PlantPreviewCharacter.objects.get_or_create(pile=pile,
                    character=character, order=order,
                    partner_site=partner_site)

            message = 'plant_preview_character: %s' % short_name
            if partner_site:
                message = '%s (%s)' % (message, partner_site)

            if created:
                message = 'Created %s' % message
            else:
                message = 'Error: did not create %s' % message
            print >> self.logfile, message

    @transaction.commit_on_success
    def _import_plant_preview_characters(self):
        print >> self.logfile, ('Setting up sample plant preview characters')

        self._create_plant_preview_characters('Lycophytes',
            ['horizontal_shoot_position_ly', 'spore_form_ly',
             'trophophyll_length_ly'])
        # Set up some different plant preview characters for a partner site.
        self._create_plant_preview_characters('Lycophytes',
            ['trophophyll_form_ly', 'upright_shoot_form_ly',
             'sporophyll_orientation_ly'], 'montshire')

        self._create_plant_preview_characters('Non-Orchid Monocots',
            ['anther_length_nm', 'leaf_arrangement_nm'])


    @transaction.commit_on_success
    def _import_lookalikes(self, db, filename):
        log.info('Loading look-alike plants from file: %s', filename)
        lookalike_table = db.table('core_lookalike')
        taxon_map = db.map('core_taxon', 'scientific_name', 'id')

        for row in open_csv(filename):
            if row['lookalike_tips'] == '':
                continue

            # Clean up Windows dash characters.
            tips = row['lookalike_tips'].replace(u'\u2013', '-')

            parts = re.split('(\w+ \w+):', tips)   # Split on plant name
            parts = parts[1:]   # Strip the first item, which is empty

            for lookalike, how_to_tell in zip(parts[0::2], parts[1::2]):
                lookalike_table.get(
                    taxon_id=taxon_map[row['scientific__name']],
                    ).set(
                    lookalike_scientific_name=lookalike.strip(),
                    lookalike_characteristic=how_to_tell.strip(),
                    )

        lookalike_table.save()

    def _set_youtube_id(self, name, youtube_id, pilegroup=False):
        if pilegroup:
            p = models.PileGroup.objects.get(name=name)
        else:
            p = models.Pile.objects.get(name=name)
        if not p.youtube_id:
            p.youtube_id = youtube_id
        p.save()


    @transaction.commit_on_success
    def _import_distributions(self, distributionsf):
        print >> self.logfile, 'Importing distribution data (BONAP)'

        db = bulkup.Database(connection)
        distribution = db.table('core_distribution')

        for row in open_csv(distributionsf):
            distribution.get(
                scientific_name=row['scientific_name'],
                state=row['state'],
                county=row['county'],
                ).set(
                status=row['status'],
                )

        distribution.save()

    @transaction.commit_on_success
    def _import_extra_demo_data(self):
        print >> self.logfile, 'Setting up demo Pile attributes'
        pile = models.Pile.objects.get(name='Woody Angiosperms')
        if not pile.key_characteristics:
            pile.key_characteristics = \
                '<ul><li>A key characteristic</li><li>Another one</li></ul>'
        if not pile.notable_exceptions:
            pile.notable_exceptions = \
                '<ul><li>An Exception</li><li>Another one</li></ul>'
        if not pile.description:
            pile.description = 'A description of the Woody Angiosperms pile'
        pile.save()

        pile = models.PileGroup.objects.get(name='Woody Plants')
        if not pile.key_characteristics:
            pile.key_characteristics = \
                '<ul><li>A key characteristic</li><li>Another one</li></ul>'
        if not pile.notable_exceptions:
            pile.notable_exceptions = \
                '<ul><li>An Exception</li><li>Another one</li></ul>'
        if not pile.description:
            pile.description = 'A description of the Woody Plants pile group'
        pile.save()

        # Set up YouTube videos for all pile groups and piles.
        TEMP_VIDEO_ID1 = 'LQ-jv8g1YVI'
        TEMP_VIDEO_ID2 = 'VWDc9oyBj5Q'

        VIDEO_INTRO   = '4zwyQiUbJv0'
        VIDEO_AQUATIC = 'GGk8ehlJqO8'
        VIDEO_LYCOPHYTES = 'AW9OXoTt5F8'
        VIDEO_FERNS = 'yXZ3H_QHnxc'
        VIDEO_GRAMINOIDS = '9GfTL4r19ag'
        VIDEO_WOODY_PLANTS = 'X5Pe0UJx_uU'
        VIDEO_NON_ORCHID_MONOCOTS = 'fPmlPnosWf8'

        self._set_youtube_id('Ferns', VIDEO_FERNS, pilegroup=True)
        self._set_youtube_id('Woody Plants', VIDEO_WOODY_PLANTS, pilegroup=True)
        self._set_youtube_id('Aquatic Plants', VIDEO_AQUATIC, pilegroup=True)
        self._set_youtube_id('Graminoids', VIDEO_GRAMINOIDS, pilegroup=True)
        self._set_youtube_id('Monocots', TEMP_VIDEO_ID1, pilegroup=True)
        self._set_youtube_id('Non-Monocots', TEMP_VIDEO_ID2, pilegroup=True)
        self._set_youtube_id('Equisetaceae', TEMP_VIDEO_ID2)
        self._set_youtube_id('Lycophytes', VIDEO_LYCOPHYTES)
        self._set_youtube_id('Monilophytes', TEMP_VIDEO_ID2)
        self._set_youtube_id('Woody Angiosperms', TEMP_VIDEO_ID1)
        self._set_youtube_id('Woody Gymnosperms', TEMP_VIDEO_ID2)
        self._set_youtube_id('Non-Thalloid Aquatic', TEMP_VIDEO_ID1)
        self._set_youtube_id('Thalloid Aquatic', TEMP_VIDEO_ID2)
        self._set_youtube_id('Carex', TEMP_VIDEO_ID1)
        self._set_youtube_id('Poaceae', TEMP_VIDEO_ID2)
        self._set_youtube_id('Remaining Graminoids', TEMP_VIDEO_ID1)
        self._set_youtube_id('Non-Orchid Monocots', VIDEO_NON_ORCHID_MONOCOTS)
        self._set_youtube_id('Orchid Monocots', TEMP_VIDEO_ID1)
        self._set_youtube_id('Composites', TEMP_VIDEO_ID2)
        self._set_youtube_id('Remaining Non-Monocots', TEMP_VIDEO_ID1)


    def _create_about_gobotany_page(self):
        help_page, created = HelpPage.objects.get_or_create(
            title='About Go-Botany', url_path='/help/')
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
            title='Getting Started', url_path='/help/start/')
        if created:
            print >> self.logfile, u'  New Help page: ', help_page

        blurb, created = Blurb.objects.get_or_create(
            name='getting_started',
            text='this is the blurb called getting_started')
        help_page.blurbs.add(blurb)

        TEMP_VIDEO_ID = 'LQ-jv8g1YVI'
        VIDEO_INTRO   = '4zwyQiUbJv0'
        blurb, created = Blurb.objects.get_or_create(
            name='getting_started_youtube_id',
            text=VIDEO_INTRO)
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
            url_path='/help/collections/')
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
            title='Video Help Topics', url_path='/help/video/')
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
        db = bulkup.Database(connection)

        terms = db.map('core_glossaryterm', 'term')
        letters = set(t[0].lower() for t in terms if t[0].isalpha())

        # Make sure a glossary page is registered for each letter for
        # which at least one glossary term exists.

        ghp_table = db.table('simplekey_glossaryhelppage')
        for letter in letters:
            ghp_table.get(
                letter=letter,
                ).set(
                title='Glossary: ' + letter.upper(),
                url_path='/help/glossary/' + letter + '/',
                )
        ghp_table.save()

        # Add every term to its appropriate glossary page.

        ghp_ids = db.map('simplekey_glossaryhelppage', 'letter', 'id')
        term_ids = db.map('core_glossaryterm', 'term', 'id')

        multi = db.table('simplekey_glossaryhelppage_terms')
        for term in terms:
            letter = term[0].lower()
            multi.get(
                glossaryhelppage_id=ghp_ids[letter],
                glossaryterm_id=term_ids[term],
                )
        multi.save()


    def _import_help(self):
        print >> self.logfile, 'Setting up help pages and content'

        # Create Help page model records to be used for search engine indexing
        # and ideally also by the page templates.
        self._create_about_gobotany_page()
        self._create_getting_started_page()
        self._create_understanding_plant_collections_page()
        self._create_video_help_topics_page()
        self._create_glossary_pages()


    @transaction.commit_on_success
    def _import_search_suggestions(self):
        print >> self.logfile, 'Setting up search suggestions'

        db = bulkup.Database(connection)
        terms = set()

        terms.update(db.map('core_family', 'name'))
        terms.update(db.map('core_family', 'common_name'))
        terms.update(db.map('core_genus', 'name'))
        terms.update(db.map('core_taxon', 'scientific_name'))
        terms.update(db.map('core_commonname', 'common_name'))
        terms.update(db.map('core_synonym', 'scientific_name'))
        terms.update(db.map('core_pilegroup', 'name'))
        terms.update(db.map('core_pile', 'name'))
        terms.update(db.map('core_glossaryterm', 'term'))
        terms.update(db.map('core_character', 'friendly_name'))

        table = db.table('simplekey_searchsuggestion')
        for term in terms:
            table.get(term=term)
        table.save()

# Import (well, for right now, just print out diagnoses about!) a
# partner species list Excel spreadsheet.

@transaction.commit_on_success
def import_partner_species(partner_short_name, excel_path):
    book = xlrd.open_workbook(excel_path)
    sheet = book.sheet_by_index(0)

    partner = models.PartnerSite.objects.get(short_name=partner_short_name)
    specieslist = sorted(models.Taxon.objects.all(),
                         key=attrgetter('scientific_name'))

    cells = sheet.col(1)[1:]  # skip first row; it contains the column title
    theirs = set(' '.join(c.value.split()[:2]) for c in cells)
    ours = set(s.scientific_name for s in specieslist)

    knowns = theirs & ours
    unknowns = theirs - ours

    print 'We list', len(ours), 'species'
    print 'They list', len(theirs), 'species'
    print 'We know about', len(knowns), 'of their species'
    if unknowns:
        print 'That leaves', len(unknowns), 'species we have not heard of:'
        for name in sorted(unknowns):
            print '   ', repr(name)

    print
    for species in specieslist:
        ps = models.PartnerSpecies.objects.filter(
            species=species, partner=partner)
        if ps and species.scientific_name not in theirs:
            print 'Removing', species.scientific_name
            ps[0].delete()
        elif not ps and species.scientific_name in theirs:
            print 'Adding', species.scientific_name
            models.PartnerSpecies(species=species, partner=partner).save()

# Parse the command line.

def main():
    start_logging()
    importer = Importer()
    name = sys.argv[1].replace('-', '_')  # like 'partner_sites'
    method = getattr(importer, '_import_' + name, None)
    modern = name in (
        'partner_sites', 'pile_groups', 'piles', 'habitats', 'taxa',
        'characters', 'character_values', 'glossary', 'lookalikes',
        'constants', 'places', 'taxon_character_values',
        'character_images', 'character_value_images', 'glossary_images',
        )  # keep old commands working for now!
    if modern and method is not None:
        db = bulkup.Database(connection)
        filenames = sys.argv[2:]
        method(db, *filenames)
        return

    # Incredibly lame option parsing, since we can't rely on real option
    # parsing
    if sys.argv[1] == 'partner':
        import_partner_species(*sys.argv[2:])
    elif sys.argv[1] == 'species-images':
        species_image_dir = os.path.join(settings.MEDIA_ROOT, 'species')
        importer.import_species_images(species_image_dir, *sys.argv[2:])
    elif sys.argv[1] == 'home-page-images':
        home_page_image_dir = os.path.join(settings.MEDIA_ROOT,
                                           'content_images')
        importer.import_home_page_images(home_page_image_dir, *sys.argv[2:])
    elif sys.argv[1] == 'distributions':
        importer._import_distributions(sys.argv[2])
    else:
        log.error('command not recognized: %r', sys.argv[1])

if __name__ == '__main__':
    main()

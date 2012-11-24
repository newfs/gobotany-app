import argparse
import csv
import gzip
import inspect
import logging
import os
import re
import shutil
import sys
import xlrd
import zipfile
from BeautifulSoup import BeautifulSoup
from collections import defaultdict
from functools import partial
from operator import attrgetter

# The GoBotany settings have to be imported before most of Django.
from gobotany import settings
from gobotany.core import rebuild
from django.core import management
management.setup_environ(settings)

from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.template.defaultfilters import slugify

import bulkup
from gobotany.core import models
from gobotany.core.pile_suffixes import pile_suffixes
from gobotany.search.models import (GroupsListPage, PlainPage,
                                    SubgroupResultsPage, SubgroupsListPage)
from gobotany.simplekey.groups_order import ordered_pilegroups, ordered_piles
from gobotany.site.models import SearchSuggestion

DEBUG=False
log = logging.getLogger('gobotany.import')

def start_logging():
    # Log everything to the import.log file.

    logging.basicConfig(filename='import.log', level=logging.DEBUG)
    logging.getLogger('boto').setLevel(logging.WARN)
    logging.getLogger('django').setLevel(logging.WARN)

    # Log only INFO and above to the console.

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s  %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def open_csv(data_file, lower=True):
    """Our CSVs are produced on Windows and sometimes re-saved from a Mac.

    This means we have to be careful about both their encoding and the
    line endings.  Note that the file must be read as bytes, parsed by
    the CSV module, and then decoded field-by-field; trying to decode
    the file with codecs.open() causes an exception in the csv module.

    """
    w = 'Windows-1252'
    r = csv.reader(data_file.open())
    names = [ name.decode(w) for name in r.next() ]
    if lower:
        names = [ name.lower() for name in names ]
    for row in r:
        yield dict(zip(names, (s.decode(w) for s in row)))

class CSVReader(object):

    def __init__(self, data_file):
        self.data_file = data_file

    def read(self):
        r = csv.reader(self.data_file.open(), dialect=csv.excel, delimiter=',')
        for row in r:
            yield [c.decode('Windows-1252') for c in row]

state_names = {
    'ct': u'Connecticut',
    'ma': u'Massachusetts',
    'me': u'Maine',
    'nh': u'New Hampshire',
    'ri': u'Rhode Island',
    'vt': u'Vermont',
    }

# Precendence of distribution status to be assigned
# when a species has differing status per subspecies
# or variety.  Higher values will override lower.
status_precedence = {
    'Species noxious' : 16,
    'present, non-native' : 15,   # New England data value
    'Species present in state and exotic' : 14,
    'Species exotic and present' : 13,
    'Species waif' : 12,
    'present, native' : 11,   # New England data value
    'Species present in state and native' : 10,
    'Species present and not rare' : 9,
    'Species native, but adventive in state' : 8,
    'Species present and rare' : 7,
    'Species extirpated (historic)' : 6,
    'Species extinct' : 5,
    'Species not present in state' : 4,
    'Species eradicated' : 3,
    'Questionable Presence (cross-hatched)' : 2,
    'absent' : 1,   # New England data value
    '' : 0,
}

def get_default_filters_from_csv(pile_name, characters_csv):
    iterator = iter(CSVReader(characters_csv).read())
    colnames = [x.lower() for x in iterator.next()]
    filters = []
    for cols in iterator:
        row = dict(zip(colnames, cols))

        if row['pile'].lower() == pile_name.lower():
            if 'default_question' in row and row['default_question'] != '':
                character_name = row['character']
                order = row['default_question']

                im = Importer()
                short_name = im.character_short_name(character_name)

                filters.append((order, short_name))

    default_filter_characters = []
    filters.sort()
    for f in filters:
        character_name = f[1]
        try:
            character = models.Character.objects.get( \
                short_name=character_name)
            default_filter_characters.append(character)
        except models.Character.DoesNotExist:
            print "Error: Character does not exist: %s" % character_name
            continue

    return default_filter_characters


class Importer(object):

    def character_short_name(self, raw_character_name):
        """Return a short name for a character, to be used in the database."""
        short_name = raw_character_name
        short_name = short_name.replace('_min', '')
        short_name = short_name.replace('_max', '')
        return short_name

    def import_constants(self, db, characters_csv):
        """Invoke all imports not requiring input or I/O"""
        self.import_plant_preview_characters(characters_csv)
        self.import_plain_pages()
        self.import_simple_key_pages()
        self.import_search_suggestions()

    def import_copyright_holders(self, db, copyright_holders_csv):
        """Load copyright holders from a CSV file"""
        log.info('Setting up copyright holders')
        copyright_holder = db.table('core_copyrightholder')

        for row in open_csv(copyright_holders_csv):
            copyright_holder.get(
                coded_name=row['coded_name'],
                ).set(
                expanded_name=row['expanded_name'],
                copyright=row['copyright'],
                source=row['image_source'],
                )

        copyright_holder.save()

    def import_wetland_indicators(self, db, wetland_indicators_csv):
        """Load wetland indicators from a CSV file"""
        log.info('Setting up wetland indicators')
        wetland_indicator = db.table('core_wetlandindicator')

        for row in open_csv(wetland_indicators_csv):
            wetland_indicator.get(
                code = row['code'],
                ).set(
                name = row['name'],
                friendly_description = row['friendly_description'],
                sequence = int(row['sequence']),
                )

        wetland_indicator.save()

    def import_partner_sites(self, db):
        """Create 'gobotany' and 'montshire' partner site objects"""
        log.info('Setting up partner sites')
        partnersite = db.table('core_partnersite')

        for short_name in ['gobotany', 'montshire']:
            partnersite.get(short_name=short_name)

        partnersite.save()

    def import_pile_groups(self, db, pilegroupf):
        """Load pile groups from a CSV file"""
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
                )

        pilegroup.save()

    def import_piles(self, db, pilef):
        """Load piles from a CSV file"""
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
                )

        pile.save()

    def import_habitats(self, db, habitatsf):
        """Load habitat list from a CSV file"""
        log.info('Setting up habitats')
        habitat = db.table('core_habitat')

        for row in open_csv(habitatsf):
            habitat.get(
                name=row['desc'],
                ).set(
                friendly_name=row['friendly_text'],
                )

        habitat.save()


    def _get_state_status(self, state_code, distribution,
                          conservation_status_code=None, is_invasive=False,
                          is_prohibited=False):
        status = ['absent']

        for state in distribution:
            if state == state_code:
                status = ['present']

                # Most further status information applies only to plants that
                # are present.

                if conservation_status_code == 'E':
                    status.append('endangered')
                elif conservation_status_code == 'T':
                    status.append('threatened')
                elif conservation_status_code in ['SC', 'SC*']:
                    status.append('special concern')
                elif conservation_status_code == 'H':
                    status.append('historic')
                elif conservation_status_code in ['C', 'WL', 'W', 'Ind']:
                    status.append('rare')

                if is_invasive == True:
                    status.append('invasive')

        # Extinct status ('X') applies to plants that are absent or present.
        # Map these to 'extirpated.'
        if conservation_status_code == 'X':
            # If status is just 'present' or 'absent' so far, clear it so
            # that 'extirpated' appears alone.
            if status == ['present'] or status == ['absent']:
                status = []
            status.append('extirpated')

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
            # Start with the generic name and epithet.
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

    def import_taxa(self, db, taxaf):
        """Load species list from a CSV file"""
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

        # Make sure some important columns are present.
        # (This is not yet an exhaustive list of required column names.)
        REQUIRED_COLUMNS = ['distribution', 'invasive_in_which_states',
                            'prohibited_from_sale_states', 'habitat']
        iterator = iter(open_csv(taxaf))
        colnames = [x for x in iterator.next()]
        for column in REQUIRED_COLUMNS:
            if column not in colnames:
                log.error('Required column missing from taxa.csv: %s', column)

        # For columns where multiple delimited values are allowed, look for
        # the expected delimiter. (It's been known to change in the Access
        # exports, quietly resulting in bugs.)
        MULTIVALUE_COLUMNS = ['distribution', 'invasive_in_which_states',
                              'prohibited_from_sale_states', 'habitat']
        EXPECTED_DELIMITER = '| '
        for column in MULTIVALUE_COLUMNS:
            delimiter_found = False
            for row in open_csv(taxaf):
                if row[column].find(EXPECTED_DELIMITER) > 0:
                    delimiter_found = True
                    break
            if not delimiter_found:
                log.error('Expected delimiter "%s" not found taxa.csv '
                          'column: %s' % (EXPECTED_DELIMITER, column))

        # Get the list of wetland indicator codes and associated text.
        # These values will be added to the taxon records as needed.
        # TODO: Consider making the taxon model just have a foreign key
        # relation to WetlandIndicator instead of a code and text field,
        # which requires some knowledge of how to import this with the
        # current approach of bulk loading and updating tables.
        wetland_indicators = dict(models.WetlandIndicator.objects.values_list(
            'code', 'friendly_description'))

        # Start import.
        family_map = db.map('core_family', 'name', 'id')
        genus_map = db.map('core_genus', 'name', 'id')

        for row in open_csv(taxaf):

            family_name = row['family']
            genus_name = row['scientific__name'].split()[0]

            # Create a Taxon.
            taxon_proxy_id = row['scientific__name']

            variety_notes = ''
            try:
                # TODO: Get the real name of this column from Sid
                variety_notes = row['variety_notes']
            except KeyError:
                # This should only happen before the CSV 
                # data has the new column added.
                pass

            # Add a simple check for data consistency
            try:
                family_id = family_map[family_name]
            except KeyError:
                # For now we're going to create a "placeholder" family for any
                # family missing from the data file, so that we can avoid
                # import problems while the data files are still being
                # completed.
                log.warn('Missing family name: %r', family_name)
                family_table.get(
                    name=family_name,
                    ).set(
                    common_name='',
                    description='',
                    )

            try:
                genus_id = genus_map[genus_name]
            except KeyError:
                # For now we're going to create a "placeholder" family for any
                # family missing from the data file, so that we can avoid
                # import problems while the data files are still being
                # completed.
                log.warn('Missing genus name: %r', genus_name)
                genus_table.get(
                    name=genus_name,
                    ).set(
                    common_name='',
                    description='',
                    family_id=family_name,
                    )

            # Get the wetland indicator category if present.
            # Only one wetland indicator per plant is imported because
            # wetland indicator categories represent non-overlapping,
            # mutually exclusive probability ranges. If the taxon record
            # has more than one indicator, the first is used.
            wetland_code = None
            wetland_text = None
            if (row['wetland_status'] != '' and
                row['wetland_status'].lower() != 'unclassified'):
                wetland_code = row['wetland_status'].split('|')[0].strip()
                wetland_text = wetland_indicators[wetland_code]

            # A plant can be marked as both native to North America and
            # introduced. This is for some native plants that are also
            # native to places elsewhere in the world, or that have
            # varieties native to North America as well as varieties native
            # elsewhere, or that have cultivated varieties that may have
            # escaped. These are marked both Yes and No in the source data.
            native_data_value = row['native_to_north_america'].lower()
            north_american_native = None
            if len(native_data_value) > 0:
                if 'yes' in native_data_value:
                    north_american_native = True
                else:
                    north_american_native = False
            north_american_introduced = None
            if len(native_data_value) > 0:
                if 'no' in native_data_value:
                    north_american_introduced = True
                else:
                    north_american_introduced = False

            taxon = taxon_table.get(
                scientific_name=row['scientific__name'],
                ).set(
                family_id=family_name,
                genus_id=genus_name,
                taxonomic_authority=row['taxonomic_authority'],
                habitat=row['habitat'],
                habitat_general='',
                factoid=row['factoid'],
                wetland_indicator_code=wetland_code,
                wetland_indicator_text=wetland_text,
                north_american_native=north_american_native,
                north_american_introduced=north_american_introduced,
                distribution=row['distribution'],
                invasive_in_states=row['invasive_in_which_states'],
                sale_prohibited_in_states=row['prohibited_from_sale_states'],
                description='',
                variety_notes=variety_notes,
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
                    pile_slug = pile_name.strip().lower().replace(' ', '-')
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
        family_map = db.map('core_family', 'name', 'id')
        genus_table.replace('family_id', family_map)
        genus_table.save()
        genus_map = db.map('core_genus', 'name', 'id')
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

    def import_families(self, db, family_file):
        """Load botanic families from a CSV file"""
        log.info('Loading families from file: %s', family_file)

        family_table = db.table('core_family')

        # Make sure some important columns are present.
        # (This is not yet an exhaustive list of required column names.)
        REQUIRED_COLUMNS = ['family', 'family_common_name', 
                'description_revised']
        iterator = iter(open_csv(family_file))
        colnames = [x for x in iterator.next()]
        for column in REQUIRED_COLUMNS:
            if column not in colnames:
                log.error('Required column missing from family.csv: %s', column)

        # Start import.

        for row in open_csv(family_file):
            family_name = row['family']
            family_table.get(
                name=family_name,
                ).set(
                common_name=row['family_common_name'],
                description=row['description_revised'],
                )

        family_table.save()

    def import_genera(self, db, genera_file):
        """Load genus data from a CSV file"""
        log.info('Loading genera from file: %s', genera_file)

        genus_table = db.table('core_genus')

        # Make sure some important columns are present.
        # (This is not yet an exhaustive list of required column names.)
        REQUIRED_COLUMNS = ['family', 'genus', 'genus_common_name', 
                'description_revised']
        iterator = iter(open_csv(genera_file))
        colnames = [x for x in iterator.next()]
        for column in REQUIRED_COLUMNS:
            if column not in colnames:
                log.error('Required column missing from genera.csv: %s', column)

        family_map = db.map('core_family', 'name', 'id')

        # Start import.

        for row in open_csv(genera_file):
            family_name = row['family']

            # Add a simple check for data consistency
            try:
                family_id = family_map[family_name]
            except KeyError:
                log.error('Bad family name: %r', family_name)
                continue

            genus_name = row['genus']
            genus_table.get(
                name=genus_name,
                ).set(
                common_name=row['genus_common_name'],
                description=row['description_revised'],
                family_id=family_id,
                )

        genus_table.save()

    def import_plant_name_suggestions(self, taxaf):
        log.info('Setting up plant name suggestions')

        db = bulkup.Database(connection)
        names = set()

        names.update(db.map('core_taxon', 'scientific_name'))
        names.update(db.map('core_commonname', 'common_name'))
        names.update(db.map('core_synonym', 'scientific_name'))

        # Populate records for model PlantNameSuggestion
        table = db.table('site_plantnamesuggestion')
        for name in names:
            table.get(name=name)
        table.save()


    def import_taxon_character_values(self, db, *filenames):
        """Load taxon character values from CSV files"""

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

    def import_characters(self, db, filename):
        """Load characters from a CSV file"""
        log.info('Loading characters from file: %s', filename)

        charactergroup_table = db.table('core_charactergroup')
        character_table = db.table('core_character')

        # Create a pile_map {'_ca': 8, '_nm': 9, ...}
        pile_map1 = db.map('core_pile', 'slug', 'id')
        pile_map = dict(('_' + suffix, pile_map1[slugify(name)])
                        for (suffix, name) in pile_suffixes.iteritems()
                        if slugify(name) in pile_map1  # for tests.py
                        )

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

            suffix = character_name[-3:]  # '_ca', etc.
            pile_id = pile_map.get(suffix)

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
                pile_id=pile_id,
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

    def import_character_images(self, db, data_source_name):
        """Load character images from a CSV file (queries S3)"""

        fileopener = get_data_fileopener(data_source_name)
        csvfile = fileopener('characters.csv')

        log.info('Fetching list of S3 character images')
        field = models.Character._meta.get_field('image')
        directories, image_names = default_storage.listdir(field.upload_to)

        log.info('Saving character image paths to database')
        character_table = db.table('core_character')
        existing_short_names = db.map('core_character', 'short_name')

        # Prepare to wipe out all existing image paths that do not get
        # restored during the following loop.

        for short_name in existing_short_names:
            character_table.get(short_name=short_name).set(image=None)

        # Process the CSV file.

        count = 0
        for row in open_csv(csvfile):

            image_name = row['image_name']
            if not image_name:
                continue
            if image_name not in image_names:
                log.error('  Missing character image: %s' % image_name)
                continue

            short_name = self.character_short_name(row['character'])
            if short_name not in existing_short_names:
                log.error('  Missing character: %s' % short_name)
                continue

            path = field.upload_to + '/' + image_name
            character_table.get(short_name=short_name).set(image=path)
            count += 1

        character_table.save()

        log.info('Done loading %d character images' % count)

    def _clean_up_html(self, html):
        """Clean up HTML ugliness arising from Access rich text export."""

        # Get rid of non-breaking spaces. These are sometimes seen in the data
        # when a sentence ends (after a period and a regular space).
        html = html.replace('&nbsp;', '')

        # Get rid of any <font> tags.
        html = re.sub(r'<\/?font.*?>', '', html)

        return html

    def import_character_values(self, db, filename):
        """Load character values from a CSV file"""
        log.info('Loading character values from: %s', filename)
        character_map = db.map('core_character', 'short_name', 'id')
        charactervalue_table = db.table('core_charactervalue')

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

            charactervalue_table.get(
                character_id=character_id,
                value_str=value_str,
                ).set(
                friendly_text=self._clean_up_html(row['friendly_text'])
                )

        charactervalue_table.save()

    def import_character_value_images(self, db, data_source_name):
        """Load character value images from a CSV (queries S3)"""

        fileopener = get_data_fileopener(data_source_name)
        csvfile = fileopener('character_values.csv')

        log.info('Fetching list of S3 character value images')
        field = models.Character._meta.get_field('image')
        directories, image_names = default_storage.listdir(field.upload_to)

        log.info('Saving character-value image paths to database')
        character_map = db.map('core_character', 'short_name', 'id')
        charactervalue_table = db.table('core_charactervalue')

        # Prepare to wipe out all existing image paths that do not get
        # restored during the following loop.

        existing_charactervalues = db.map('core_charactervalue',
                                          ('character_id', 'value_str'))

        for character_id, value_str in existing_charactervalues:
            if not value_str:
                continue
            charactervalue_table.get(
                character_id=character_id, value_str=value_str
                ).set(
                image=None
                )

        # Process the CSV file.

        count = 0
        for row in open_csv(csvfile):

            image_name = row['image_name']
            if not image_name:
                continue
            if image_name not in image_names:
                log.error('character value image missing: %s' % image_name)
                continue

            character_name = row['character']
            if character_name == 'family':
                continue
            if '_' not in character_name:
                log.warn('character lacks pile suffix: %r', character_name)
                continue
            pile_suffix = character_name.rsplit('_', 1)[1]
            if not pile_suffix in pile_suffixes:
                log.warn('character has bad pile suffix: %r', character_name)
                continue

            short_name = self.character_short_name(character_name)
            character_id = character_map.get(short_name)
            if character_id is None:
                log.warn('character does not exist: %r', short_name)
                continue

            value_str = row['character_value']
            if (character_id, value_str) not in existing_charactervalues:
                log.warn('character value does not exist: %r / %r',
                         short_name, value_str)
                continue

            charactervalue_table.get(
                character_id=character_id,
                value_str=value_str,
                ).set(
                image=field.upload_to + '/' + image_name,
                )
            count += 1

        charactervalue_table.save()

        log.info('Done loading %d character-value images' % count)

    def import_glossary(self, db, filename):
        """Load glossary terms from a CSV file"""
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
                is_highlighted=row['is_highlighted'],
                )

        glossaryterm_table.save()

    def import_glossary_images(self, db, data_source_name):
        """Load glossary images from 'glossary.csv'"""

        fileopener = get_data_fileopener(data_source_name)
        csvfile = fileopener('glossary.csv')

        log.info('Scanning glossary images on S3')
        field = models.GlossaryTerm._meta.get_field('image')
        directories, image_names = default_storage.listdir(field.upload_to)

        log.info('Saving glossary images to table')

        glossaryterm_table = db.table('core_glossaryterm')
        existing_terms = db.map('core_glossaryterm', 'term')
        count = 0

        for row in open_csv(csvfile):

            if not row['definition'] or row['definition'] == row['term']:
                continue

            image_name = row['illustration']
            if not image_name:
                continue
            if image_name not in image_names:
                log.error('  Unknown image: %s' % image_name)
                continue

            if row['term'] not in existing_terms:
                log.error('  Unknown term: %s' % row['term'])
                continue

            glossaryterm_table.get(
                term=row['term'],
                ).set(
                image=field.upload_to + '/' + image_name,
                )
            count += 1

        glossaryterm_table.save()

        log.info('Saved %d glossary images to table' % count)

    def _get_species_for_image_filename(self, filename):
        """Parse an image filename and return the species to which it
        pertains, with some relevant image information.
        """
        pattern = re.compile(r'(-[a-z]{2}-)')
        parts = pattern.split(filename)
        name = parts[0].split('-')
        image_type = parts[1][1:3]
        photographer = parts[2].split('-')[0]
        genus = name[0]

        # Support the use of underscores in filenames to indicate
        # hyphenated specific epithets. This is seen in the image files
        # but only for a few thus far, so a second strategy is described
        # below for handling the rest.
        epithet = name[1].replace('_', '-')

        # If there are three or four parts to the name, assume a hyphenated
        # specific epithet like Liatris novae-angliae, as seen much of
        # of the time in the data. Sometimes this will be incorrect,
        # such as when it represents a subspecific or varietal epithet,
        # or in the case of some "comparison" images, and the taxon will
        # not be found when looked up. But, the calling routine can try
        # looking up the taxon a second time omitting the portion after
        # the hyphen, which should finally find the taxon.
        if len(name) in [3, 4]:
            epithet = '-'.join([epithet, name[2]])

        # When there are many parts to the name (4+), it is likely
        # a "comparison" image containing two species names. In that
        # case we are only concerned with the first name, because
        # there exists a second, identical image with the two plant
        # names reversed for the other plant's species page.

        species = {'genus': genus,
                   'species': epithet,
                   'image_type': image_type,
                   'photographer': photographer}
        return species

    def import_taxon_images(self, db):
        """Load the ls-taxon-images.gz list from S3"""

        # Retrieve the tables and mappings we need.

        db = bulkup.Database(connection)

        table_contentimage = db.table('core_contentimage')
        table_imagetype = db.table('core_imagetype')
        pile_names = db.map('core_pile', 'id', 'name')
        taxon_ids = db.map('core_taxon', 'scientific_name', 'id')
        taxonpile_map = db.manymap('core_pile_species', 'taxon_id', 'pile_id')

        # Right now, the image categories CSV is simply used to confirm
        # that we recognize the type of every image we import.

        core_dir = os.path.dirname(os.path.abspath(__file__))
        image_categories_csv = os.path.join(core_dir, 'image_categories.csv')

        taxon_image_types = {}
        for row in open_csv(PlainFile('.', image_categories_csv)):
            # lower() is important because case is often mismatched
            # between the official name of a pile and its name here
            key = (row['pile'].lower(), row['code'])
            # The category looks like "bark, ba" so we split on the comma
            taxon_image_types[key] = row['category'].rsplit(',', 1)[0]

        # We expect our image storage to contain directories named by
        # family, with taxon images beneath them (but we ignore the
        # family name, so any two-level hierarchy of directories and
        # images should work).

        content_type_id = ContentType.objects.get_for_model(models.Taxon).id

        log.info('Scanning S3 for taxon images')

        lsgz = default_storage.open('ls-taxon-images.gz')
        ls = gzip.GzipFile(fileobj=lsgz)

        count = 0
        already_seen = set()

        for line in ls:
            image_path = line.split(' s3://newfs/')[1].strip()
            dirname, filename = image_path.rsplit('/', 1)
            if '.' not in filename:
                log.error('  file lacks an extension: %s', filename)
                continue
            if filename.count('.') > 1:
                log.error('  filename has multiple periods: %s', filename)
                continue
            name, ext = filename.split('.')
            if ext.lower() not in ('jpg', 'gif', 'png', 'tif'):
                log.error('  file lacks image extension: %s', filename)
                continue

            # With an acceptable-looking image filename, parse it to find
            # the species.

            species = self._get_species_for_image_filename(name)

            # Find the Taxon corresponding to this species.

            scientific_name = ' '.join((species['genus'],
                                        species['species'])).capitalize()
            taxon_id = taxon_ids.get(scientific_name)
            if taxon_id is None:
                # Try again, dropping any hyphenated part in the
                # specific epithet, which may have been interpreted
                # incorrectly when parsing the filename.
                scientific_name = scientific_name.rsplit('-', 1)[0]
                taxon_id = taxon_ids.get(scientific_name)

                if taxon_id is None:
                    log.error('  image names unknown taxon: %s', filename)
                    continue

            # Get the image type, now that we know what pile the
            # species belongs in.

            for pile_id in taxonpile_map[taxon_id]:
                key = (pile_names[pile_id].lower(), species['image_type'])
                if key in taxon_image_types:
                    break
            else:
                log.error('  unknown image type %r: %s',
                          species['image_type'], filename)
                continue

            # Fetch or create a row representing this image type.

            image_type_name = taxon_image_types[key]
            table_imagetype.get(name=image_type_name)

            # Arbitrarily promote the first image for each
            # species-type to Rank 1.

            rank_key = (taxon_id, image_type_name)
            if rank_key in already_seen:
                rank = 2
            else:
                rank = 1
                already_seen.add(rank_key)

            table_contentimage.get(
                object_id = taxon_id,
                content_type_id = content_type_id,
                # Use filename to know if this is the "same" image.
                image = image_path,
                ).set(
                alt = '%s: %s' % (scientific_name, image_type_name),
                creator = species['photographer'],
                description = '',
                image_type_id = image_type_name,  # replaced with id later
                rank = rank,
                )

            count += 1

        # Add image ranks to their alt descriptions.

        for row in table_contentimage:
            row.alt += ' %s' % (row.rank,)

        # Save everything to the database.

        table_imagetype.save()
        imagetype_map = db.map('core_imagetype', 'name', 'id')
        table_contentimage.replace('image_type_id', imagetype_map)
        table_contentimage.save()

        log.info('Imported %d taxon images', count)

    def import_home_page_images(self, db):
        """Load home page image URLs from S3"""
        log.info('Emptying the old home page image list')
        models.HomePageImage.objects.all().delete()

        log.info('Loading home page images')
        field = models.HomePageImage._meta._name_map['image'][0]
        directories, image_names = default_storage.listdir(field.upload_to)
        image_paths = [ field.upload_to + '/' + name
                        for name in image_names if name ]

        for path in image_paths:
            log.info('  Adding image: %s' % path)
            models.HomePageImage.objects.get_or_create(image=path)

        log.info('Loaded %d home page images' % len(image_names))

    def _has_unexpected_delimiter(self, text, unexpected_delimiter):
        """Check for an unexpected delimiter to help guard against breaking
           the app completely silently.
        """
        if text.find(unexpected_delimiter) > -1:
            log.info('  Error: unexpected delimiter:', unexpected_delimiter)
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
            log.info('  Error: habitat does not exist:', habitat_name)
        return friendly_name and friendly_name.lower()


    def import_places(self, db, taxaf):
        """Load habitat and state data from a taxa CSV file"""
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

            # Habitat (general) character values.

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
            log.info(message)

    def import_plant_preview_characters(self, characters_csv):
        """Load plant preview characters from a CSV file"""
        log.info('Setting up plant preview characters')

        # For now, plant preview characters should initially be set to
        # the same characters as are used for the default filters.
        for pile in models.Pile.objects.all():
            # Start with some characters common to all plant subgroups.
            character_short_names = ['habitat_general', 'state_distribution']
            characters = get_default_filters_from_csv(pile.name,
                                                      characters_csv)
            character_short_names.extend([character.short_name
                                          for character in characters])
            self._create_plant_preview_characters(pile.name,
                                                  character_short_names)

        # Set up some different plant preview characters for a partner site.
        # (Disabled this demo code pending partner customization decisions.)
        #self._create_plant_preview_characters('Lycophytes',
        #    ['trophophyll_form_ly', 'upright_shoot_form_ly',
        #     'sporophyll_orientation_ly'], 'montshire')

    def import_lookalikes(self, db, filename):
        """Load look-alike plants from a CSV file"""
        log.info('Loading look-alike plants from file: %s', filename)
        lookalike_table = db.table('core_lookalike')
        taxon_map = db.map('core_taxon', 'scientific_name', 'id')

        # WARNING: this routine DOES NOT remove old lookalikes if an
        # earlier run of the import routine inserted them; for the
        # moment, it knows only how to insert new ones or update
        # existing ones based on the input CSV.

        for row in open_csv(filename):
            if row['lookalike_tips'] == '':
                continue

            # Clean up Windows dash characters.
            tips = row['lookalike_tips'].replace(u'\u2013', '-')

            if tips.find(':') > 1:
                parts = re.split('(\w+ \w+):', tips)   # Split on plant name
                parts = parts[1:]   # Strip the first item, which is empty
            else:
                # Handle entries that do not yet have explanatory text.
                # In this case, multiple plants are allowed if separated
                # by a semicolon.
                parts = [(plant, '') for plant in tips.split(';')]
                parts = [item for tup in parts for item in tup]   # flatten

            for lookalike, how_to_tell in zip(parts[0::2], parts[1::2]):
                lookalike_table.get(
                    taxon_id=taxon_map[row['scientific__name']],
                    lookalike_scientific_name=lookalike.strip(),
                    ).set(
                    lookalike_characteristic=how_to_tell.strip(),
                    )

        lookalike_table.save()


    def import_distributions(self, distributionsf):
        """Load BONAP distribution data from a CSV file"""
        log.info('Importing distribution data (BONAP)')

        DEFAULT_STATUS_COLUMN_NAME = 'status'
        ADJUSTED_STATUS_COLUMN_NAME = 'edited data'

        db = bulkup.Database(connection)
        distribution = db.table('core_distribution')

        # If adjusted status data are present, import from the
        # appropriate column.
        status_column_name = DEFAULT_STATUS_COLUMN_NAME
        for row in open_csv(distributionsf):
            if row.has_key(ADJUSTED_STATUS_COLUMN_NAME.lower()):
                status_column_name = ADJUSTED_STATUS_COLUMN_NAME.lower()
            break   # Now that the correct status column name is known

        for row in open_csv(distributionsf):
            distribution.get(
                scientific_name=row['scientific_name'],
                state=row['state'],
                county=row['county'],
                ).set(
                status=row[status_column_name],
                )

            self._apply_subspecies_status(row, distribution,
                                          status_column_name)

        distribution.save()

    def _apply_subspecies_status(self, csv_row, distribution,
                                 csv_status_column_name):
        distribution_status = csv_row[csv_status_column_name]
        full_name = csv_row['scientific_name']
        state = csv_row['state']
        county = csv_row['county']

        scientific_name = _extract_scientific_name(full_name)
        if scientific_name == full_name:
            return
        # If the new scientific name indicates that this is a subspecies or variety
        # record, we will add it under the species name, modifying the
        # current distribution status if the status from this record has
        # higher precedence
        distribution_row = distribution.get(
            scientific_name=scientific_name,
            state=state,
            county=county,
            )

        # Get the current status from the distribution table row. Here
        # the field name is part of the model and does not vary, unlike
        # the source CSV data column names.
        current_status = distribution_row.__dict__.get('status') or ''

        if status_precedence[distribution_status] > status_precedence[current_status]:
            # Interesting information, but there's SO much output it's annoying normally.
            #log.info(
            #    'Species %s status overridden from subspecies %s', 
            #    scientific_name,
            #    full_name
            #)
            #log.info('New distribution status ["%s" -> "%s"]',
            #        current_status,
            #        distribution_status
            #)
            distribution_row.set(status=distribution_status)

    def import_videos(self, db, videofilename):
        """Load pile and pile group video URLs from a CSV file"""
        log.info('Reading CSV to import videos and assign to piles/pilegroups')

        # First clear any existing video associations.
        for pile_group in models.PileGroup.objects.all():
            if pile_group.video:
                pile_group.video = None
        for pile in models.Pile.objects.all():
            if pile.video:
                pile.video = None

        # Create and associate video records from the CSV file.
        for row in open_csv(videofilename):
            v, created = models.Video.objects.get_or_create(
                         title=row.get('pile-or-subpile'),
                         youtube_id=row['youtube-id'],
                         )
            log.info('    Video: %s %s' % (v.title, v.youtube_id))

            # For plant group (pile group) and subgroup (pile) videos,
            # assign proper titles, then associate with the pile group
            # or pile.
            if row['pile-or-subpile']:
                try:
                    p = models.PileGroup.objects.get(
                        name=row['pile-or-subpile'])
                    v.title = p.friendly_title
                    v.save()
                    log.info('    Pile group: %s - YouTube video id: %s' %
                             (v.title, v.youtube_id))
                except models.PileGroup.DoesNotExist:
                    try:
                        p = models.Pile.objects.get(
                            name=row['pile-or-subpile'])
                    except models.Pile.DoesNotExist:
                        log.info('      UNKNOWN: %s - YouTube video id: %s' %
                                 (row['pile-or-subpile'], v.youtube_id))
                        continue
                    v.title = p.friendly_title
                    v.save()
                    log.info('      Pile: %s - YouTube video id: %s' %
                             (v.title, v.youtube_id))

                p.video = v
                p.save()


    def _get_text_from_template(self, template_file_path):
        """Get the plain text from a template file. This is for returning
        text content for indexing by our search engine where most of the
        content is the template and marked up with HTML.
        """
        template_tags_pattern = re.compile('{[%#{].*?[%#}]}')
        attributes_pattern = re.compile('[a-z]+="[a-z \-]+"')
        require_pattern = re.compile('require\(.*\);')

        core_dir = os.path.dirname(os.path.abspath(__file__))
        gobotany_dir = os.path.dirname(core_dir)
        gobotany_app_dir = os.path.dirname(gobotany_dir)
        project_dir = os.path.join(gobotany_app_dir, 'gobotany')

        template_file = os.path.join(project_dir, template_file_path);

        f = open(template_file, 'r')
        lines = []
        for line in f:
            lines.append(line.strip())
        f.close()

        html = ' '.join(lines)
        soup = BeautifulSoup(html)
        texts = soup.findAll(text=True)
        text = ''.join(texts)

        # Get rid of some extra template bits.
        text = template_tags_pattern.sub('', text)
        text = attributes_pattern.sub('', text)
        text = require_pattern.sub('', text)

        return text


    def _create_plain_page(self, url_name, page_title, template_path=None):
        url_path = reverse(url_name)
        plain_page, created = PlainPage.objects.get_or_create(
            title=page_title, url_path=url_path)
        if created:
            log.info('  New PlainPage: %s' % plain_page)

        if template_path:
            text = self._get_text_from_template(template_path)
            log.info('    Add search text: %d characters' % len(text))
            plain_page.search_text = text
            plain_page.save()

        return plain_page


    def _create_help_page(self):
        self._create_plain_page('site-help',
                                'Help',
                                'site/templates/gobotany/help.html')


    def _create_about_gobotany_page(self):
        self._create_plain_page('site-about',
                                'About Go Botany',
                                'site/templates/gobotany/about.html')


    def _create_getting_started_page(self):
        plain_page = self._create_plain_page('site-getting-started',
            'Getting Started with the Simple Key',
            'site/templates/gobotany/getting_started.html')
        video = models.Video.objects.get(title='Getting Started')
        if video:
            plain_page.videos.add(video)
            plain_page.save()


    def _get_pile_and_group_videos(self):
        videos = []
        for pilegroup in ordered_pilegroups():
            if pilegroup.video and len(pilegroup.video.youtube_id) > 0:
                videos.append(pilegroup.video)
            for pile in ordered_piles(pilegroup):
                if pile.video and len(pile.video.youtube_id) > 0:
                    videos.append(pile.video)
        return videos


    def _create_advanced_map_page(self):
        plain_page = self._create_plain_page(
            'site-advanced-map',
            'Advanced Map to Groups',
            'site/templates/gobotany/advanced_map.html')
        # Add videos associated with each pile group and pile.
        videos = self._get_pile_and_group_videos()
        for video in videos:
            plain_page.videos.add(video)
        plain_page.save()


    def _create_video_help_topics_page(self):
        plain_page = self._create_plain_page('site-video',
                                             'Video Help Topics')
        # Add Getting Started video.
        video = models.Video.objects.get(title='Getting Started')
        if video:
            plain_page.videos.add(video)

        # Add pile group and pile videos.
        videos = self._get_pile_and_group_videos()
        for video in videos:
            plain_page.videos.add(video)

        plain_page.save()


    def _create_contributors_page(self):
        self._create_plain_page('site-contributors',
                                'Contributors',
                                'site/templates/gobotany/contributors.html')


    def _create_teaching_page(self):
        self._create_plain_page('site-teaching', 'Teaching',
                                'site/templates/gobotany/teaching.html')


    def _create_privacy_policy_page(self):
        self._create_plain_page('site-privacy', 'Privacy Policy',
                                'site/templates/gobotany/privacy.html')

    def _create_terms_of_use_page(self):
        self._create_plain_page('site-terms-of-use', 'Terms of Use',
                                'site/templates/gobotany/terms.html')


    def import_plain_pages(self):
        """Create various plain pages in the database for search"""
        log.info('Setting up plain pages (help, about, glossary, etc.)')

        # Create page model records to be used for search engine indexing
        # and ideally also by the page templates.
        self._create_help_page()
        self._create_about_gobotany_page()
        self._create_getting_started_page()
        self._create_advanced_map_page()
        self._create_video_help_topics_page()
        self._create_contributors_page()

        self._create_teaching_page()
        self._create_privacy_policy_page()
        self._create_terms_of_use_page()


    def _create_plant_groups_list_page(self):
        groups_list_page, created = GroupsListPage.objects.get_or_create(
            title='Simple Key for Plant Identification',
            main_heading='Which group best describes your plant?')
        if created:
            log.info('  New Groups List page: %s' % groups_list_page)
        # Add plant groups.
        groups = models.PileGroup.objects.all()
        for group in groups:
            groups_list_page.groups.add(group)
        groups_list_page.save()


    def _create_plant_subgroups_list_pages(self):
        groups = models.PileGroup.objects.all()
        for group in groups:
            title = '%s: Simple Key' % group.friendly_title
            subgroups_list_page, created = \
                SubgroupsListPage.objects.get_or_create(
                    title=title,
                    main_heading='Is your plant in one of these subgroups?',
                    group=group)   # Subgroups can be accessed via group
        if created:
            log.info('  New Subgroups List page: %s' % subgroups_list_page)


    def _create_plant_subgroup_results_pages(self):
        subgroups = models.Pile.objects.all()
        for subgroup in subgroups:
            title = '%s: %s: Simple Key' % (subgroup.friendly_title,
                                            subgroup.pilegroup.friendly_title)
            subgroup_results_page, created = \
                SubgroupResultsPage.objects.get_or_create(
                    title=title,
                    main_heading=subgroup.friendly_title,
                    subgroup=subgroup)   # Taxa can be accessed via subgroup
        if created:
            log.info('  New Subgroup Results page: %s' %
                     subgroup_results_page)


    def import_simple_key_pages(self):
        """Create various Simple Key pages in the database"""
        log.info('Setting up Simple Key pages')

        # Create Simple Key page model records to be used for search
        # engine indexing and also to supply some basic information to
        # the page templates.
        self._create_plant_groups_list_page()
        self._create_plant_subgroups_list_pages()
        self._create_plant_subgroup_results_pages()


    def import_search_suggestions(self):
        """Set up the search-suggestions table"""
        log.info('Setting up search suggestions')

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

        # Populate records for model SearchSuggestion
        table = db.table('site_searchsuggestion')
        for term in terms:
            term = term.lower()
            table.get(term=term)
        table.save()

        # Add extra search suggestions for the Simple Key pages.
        groups_list_page = GroupsListPage.objects.all()[0]
        suggestions = groups_list_page.search_suggestions()
        groups = SubgroupsListPage.objects.all()
        for group in groups:
            suggestions.extend(group.search_suggestions())
        subgroups = SubgroupResultsPage.objects.all()
        for subgroup in subgroups:
            suggestions.extend(subgroup.search_suggestions())

        # Add extra search suggestions for the "generic" portion
        # of common names, for example, "dogwood" from "silky dogwood."
        for name in models.CommonName.objects.all():
            parts = name.common_name.split(' ')
            if len(parts) > 1:
                suggestions.append(parts[-1])

        suggestions = list(set(suggestions))   # remove duplicates
        for suggestion in suggestions:
            suggestion = suggestion.lower()
            s, created = SearchSuggestion.objects.get_or_create(
                term=suggestion)
            if created:
                log.info('  New SearchSuggestion: %s' % suggestion)


# Import a partner species list Excel spreadsheet.

def import_partner_species(partner_short_name, excel_file):
    """Load a partner species list from an Excel file"""
    book = xlrd.open_workbook(file_contents=excel_file.open('r').read())
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

# Routines for doing full import.

full_import_steps = (
    (Importer.import_partner_sites,),
    (Importer.import_pile_groups, 'pile_group_info.csv'),
    (Importer.import_piles, 'pile_info.csv'),
    (Importer.import_habitats, 'habitats.csv'),
    (Importer.import_families, 'families.csv'),
    (Importer.import_genera, 'genera.csv'),
    (Importer.import_wetland_indicators, 'wetland_indicators.csv'),
    (Importer.import_taxa, 'taxa.csv'),
    (Importer.import_characters, 'characters.csv'),
    (Importer.import_character_values, 'character_values.csv'),
    (Importer.import_glossary, 'glossary.csv'),
    (Importer.import_lookalikes, 'lookalikes-raw.csv'),
    (Importer.import_places, 'taxa.csv'),
    (Importer.import_videos, 'videos.csv'),
    (Importer.import_constants, 'characters.csv'),
    (Importer.import_copyright_holders, 'copyright_holders.csv'),
    (Importer.import_plant_name_suggestions, 'taxa.csv'),

    (Importer.import_distributions,
     'New-England-tracheophyte-county-level-nativity.csv'),
    (Importer.import_distributions, 'bonap-north-america.csv'),

    (Importer.import_taxon_character_values,
     'pile_angiosperms_1.csv',
     'pile_angiosperms_1a.csv',
     'pile_angiosperms_2.csv',
     'pile_angiosperms_3.csv',
     'pile_carex_1.csv',
     'pile_carex_2.csv',
     'pile_composites_1.csv',
     'pile_composites_2.csv',
     'pile_composites_3.csv',
     'pile_composites_4.csv',
     'pile_composites_5.csv',
     'pile_equisetaceae.csv',
     'pile_gymnosperms_1.csv',
     'pile_gymnosperms_2.csv',
     'pile_lycophytes.csv',
     'pile_monilophytes.csv',
     'pile_non_orchid_monocots_1.csv',
     'pile_non_orchid_monocots_2.csv',
     'pile_non_orchid_monocots_3.csv',
     'pile_non_thalloid_aquatics_1a.csv',
     'pile_non_thalloid_aquatics_1b.csv',
     'pile_non_thalloid_aquatics_2.csv',
     'pile_orchid_monocots.csv',
     'pile_poaceae_1.csv',
     'pile_poaceae_1a.csv',
     'pile_poaceae_2.csv',
     'pile_remaining_graminoids_1a.csv',
     'pile_remaining_graminoids_1b.csv',
     'pile_remaining_non_monocots_1.csv',
     'pile_remaining_non_monocots_2.csv',
     'pile_remaining_non_monocots_2a.csv',
     'pile_remaining_non_monocots_2b.csv',
     'pile_remaining_non_monocots_3.csv',
     'pile_remaining_non_monocots_3a.csv',
     'pile_remaining_non_monocots_3b.csv',
     'pile_remaining_non_monocots_4.csv',
     'pile_remaining_non_monocots_5.csv',
     'pile_remaining_non_monocots_6.csv',
     'pile_remaining_non_monocots_7.csv',
     'pile_remaining_non_monocots_8.csv',
     'pile_thalloid_aquatics.csv',
     ),

    (import_partner_species, '!montshire', 'montshire-species-list.xls'),
    (rebuild.rebuild_default_filters, 'characters.csv'),
    (rebuild.rebuild_plant_of_the_day, '!SIMPLEKEY'),
    )


class CannotOpen(Exception):
    """An import file cannot be opened."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'Cannot open import file: %s' % (self.name,)


class PlainFile(object):
    """Plain file, behind the same uniform interface as ZipMember."""

    def __init__(self, directory, name):
        self.path = os.path.join(directory, name)
        self.openfiles = []

    def __str__(self):
        return self.path

    def open(self, mode='rU'):
        try:
            f = open(self.path, mode)
        except IOError:
            raise CannotOpen(self.path)
        self.openfiles.append(f)
        return f

    def close(self):
        for f in self.openfiles:
            f.close()


class ZipMember(object):
    """Member of a zip file archive that can be repeatedly opened.

    Zipfile members do not support seek() or rewind(), which causes a
    problem for several of our import routines because they open their
    target file twice.  So we always pass them an instance of this class
    instead, which our CSV iterator routines are prepared to open with
    the method below.

    """
    def __init__(self, zipfileobj, name):
        self.zipfileobj = zipfileobj
        self.name = 'csv/' + name
        self.openfiles = []

    def __str__(self):
        return self.name

    def open(self, mode='rU'):
        try:
            f = self.zipfileobj.open(self.name, mode)
        except KeyError:
            raise CannotOpen(self.name)
        self.openfiles.append(f)
        return f

    def close(self):
        for f in self.openfiles:
            f.close()


def ziplist():
    directories, filenames = default_storage.listdir('/data/')
    for filename in sorted(filenames):
        if filename:
            print filename


def get_data_fileopener(name):
    """Return a ``fileopener()`` function for opening import data files.

    The ``fileopener()`` function that this is returned by this routine
    takes one argument: the filename that you would like to open, like
    ``'genera.csv'``.  It returns an open file that you can read from.
    The ``name`` argument to this routine can have three values:

    ``None``
        The latest Go Botany data zipfile is downloaded from Amazon S3
        and its contents are searched for the files requested.

    *file-name.zip*
        A zipfile on the local filesystem can be named explicitly, in
        which case data files will be searched for inside of it.

    *directory-name*
        Instead of pulling from a compressed zip file, you can pull
        directly from data files sitting uncompressed on your file
        system by simply naming the directory.

    """
    if name is None:
        print 'Searching S3 for the most recent data zip file ...'
        directories, filenames = default_storage.listdir('/data/')
        name = sorted([ f for f in filenames if f.endswith('.zip') ])[-1]
        print 'Most recent data zip file is:'
        print
        print '   ', name
        print
        if os.path.exists(name):
            print 'Using copy already present on filesystem'
        else:
            print 'Downloading', name, '...'
            with open(name, 'w') as dst:
                with default_storage.open('/data/' + name) as src:
                    shutil.copyfileobj(src, dst)
            print 'Done'

    if os.path.isdir(name):
        fileopener = partial(PlainFile, name)
    elif os.path.isfile(name):
        try:
            zipfileobj = zipfile.ZipFile(name)
        except Exception as e:
            print >>sys.stderr, 'Error:', e
            sys.exit(1)
        fileopener = partial(ZipMember, zipfileobj)
        log.info('Data will be imported from zip file: %s', name)
    else:
        print >>sys.stderr, 'No such file or directory:', name
        sys.exit(1)

    return fileopener


def zipimport(name):
    """Does a full database load from CSV files in a zip file or directory.

    If you do not specify a filename or directory name, then an attempt
    is made to download the latest data zip file from the NEWFS "data"
    directory on Amazon S3.  A missing CSV file in the directory or zip
    file you are processing will generate a warning, but the import will
    still try to proceed without it; you can therefore run the command
    on an empty directory to see the list of zip files that are needed
    for a complete import.  Use the separate "ziplist" command if you
    need to review which zip files are available on S3.

    """
    fileopener = get_data_fileopener(name)
    importer_self = Importer()

    for step in full_import_steps:
        function = step[0]
        args = []
        if takes_self_arg(function):
            args.append(importer_self)
        if takes_db_arg(function):
            db = bulkup.Database(connection)  # fresh instance for each import!
            args.append(db)
        filenames = step[1:]
        args.extend(
            fn[1:] if fn.startswith('!') else fileopener(fn)
            for fn in filenames
            )
        print
        print 'Calling', function.__name__ + '()'
        print

        wrapped_function = transaction.commit_on_success(function)
        try:
            wrapped_function(*args)
        except CannotOpen as e:
            log.info('Canceling import step: %s', str(e))
            continue
        finally:
            for arg in args:
                if hasattr(arg, 'close'):
                    arg.close()

# Utilities.

def delete_files_in(dirname):
    for dirpart in (dirname, os.path.join('content-thumbs', dirname)):
        dirpath = os.path.join(settings.MEDIA_ROOT, dirpart)
        if os.path.isdir(dirpath):
            log.info('Deleting every file under MEDIA_ROOT/%s' % dirpart)
            shutil.rmtree(dirpath)

def _extract_scientific_name(name):
    if not ('var.' in name or 'ssp.' in name):
        return name
    # Because some plants names have both subspecies and variety--in
    # that order--check for subspecies first in order to extract correctly.
    if 'ssp.' in name:
        return name[:name.find('ssp.')].strip()
    if 'var.' in name:
        return name[:name.find('var.')].strip()

# Parse the command line.

def takes_self_arg(callable):
    spec = inspect.getargspec(callable)
    return spec.args[0:1] == ['self']

def takes_db_arg(callable):
    spec = inspect.getargspec(callable)
    if spec.args[0:1] == ['self']:
        del spec.args[0]
    return spec.args[0:1] == ['db']

def takes_data_source(callable):
    spec = inspect.getargspec(callable)
    if spec.args[0:1] == ['self']:
        del spec.args[0]
    if spec.args[0:1] == ['db']:
        del spec.args[0]
    return spec.args == ['data_source_name']

def takes_single_filename(callable):
    spec = inspect.getargspec(callable)
    if spec.args[0:1] == ['self']:
        del spec.args[0]
    if spec.args[0:1] == ['db']:
        del spec.args[0]
    return spec.args == ['filename']

def takes_many_filenames(callable):
    spec = inspect.getargspec(callable)
    if spec.args[0:1] == ['self']:
        del spec.args[0]
    if spec.args[0:1] == ['db']:
        del spec.args[0]
    return spec.varargs

def add_subcommand(subs, name, function):
    sub = subs.add_parser(name, help=function.__doc__)
    sub.set_defaults(function=function)
    if takes_data_source(function):
        sub.add_argument('data_source', nargs='?',
                         help='S3 zipfile, local zipfile, or local directory')
    elif takes_single_filename(function):
        sub.add_argument('filename', help='name of the file to load')
    elif takes_many_filenames(function):
        sub.add_argument('filenames', help='one or more files to load',
                         nargs='*')

def main():
    start_logging()
    importer = Importer()

    parser = argparse.ArgumentParser(
        description='Import one or more data files into the Go Botany database'
        )
    subs = parser.add_subparsers()
    subs.metavar = 'subcommand'

    prefix = 'import_'

    for name in dir(importer):
        if not name.startswith(prefix):
            continue
        method = getattr(importer, name)
        add_subcommand(subs, name[len(prefix):].replace('_', '-'), method)

    sub = subs.add_parser('partner', help=import_partner_species.__doc__)
    sub.set_defaults(function=import_partner_species)
    sub.add_argument('partner', help='nickname of a partner organization')
    sub.add_argument('filename', help='name of the file to load')

    sub = subs.add_parser(
        'ziplist', help='List the zip files stored on S3')
    sub.set_defaults(function=ziplist)

    sub = subs.add_parser(
        'zipimport', help='Full import from a zip file or directory',
        description=zipimport.__doc__)
    sub.set_defaults(function=zipimport)
    sub.add_argument(
        'file_or_directory', nargs='?',
        help='S3 zipfile, local zipfile, or directory; omit this argument'
        ' to force the latest zipfile to be downloaded from S3',
        )

    args = parser.parse_args()

    function = args.function
    function_args = []

    if takes_db_arg(function):
        db = bulkup.Database(connection)
        function_args.append(db)
    if hasattr(args, 'partner'):
        function_args.append(args.partner)
    if hasattr(args, 'file_or_directory'):
        function_args.append(args.file_or_directory)
    if hasattr(args, 'data_source'):
        function_args.append(args.data_source)
    if hasattr(args, 'filename'):
        function_args.append(PlainFile('.', args.filename))
    if hasattr(args, 'filenames'):
        function_args.extend(PlainFile('.', f) for f in args.filenames)

    wrapped_function = transaction.commit_on_success(function)
    wrapped_function(*function_args)

if __name__ == '__main__':
    main()

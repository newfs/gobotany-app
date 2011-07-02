"""Report on data coverage for all species in the Go Botany data set."""

import csv
import fnmatch
import locale
import os
import re
import sys

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


class DataCoverageChecker(object):

    def __init__(self, data_directory_path):
        locale.setlocale(locale.LC_ALL, 'en_US')
        self.data_directory_path = data_directory_path
        # Initialize what will be a full list of species and Simple Key
        # flags, used for reference when building the data set later.
        self.species = {}
        # Initialize a dictionary where a full data set will be built.
        # Data set structure:
        # { 'pile1': { 'sci_name1': { 'simple_key': True/False,
        #                             'character_data: {
        #                                 'char1': 'val1',
        #                                 'char2': 'val2', ...
        #                                 }
        #                           },
        #              'sci_name2': { ... },
        #              ...
        #            },
        #   'pile2': { ... },
        #   ...
        # }
        self.data_set = {}

    def _get_initialized_species(self, scientific_name, is_in_simple_key):
        return {
            'simple_key': is_in_simple_key,
            'character_data': {}
        }

    def _add_all_species(self):
        '''Collect all the species and whether each is in the Simple Key for
           reference later when going through pile by pile.'''
        taxa_file_path = self.data_directory_path + '/taxa.csv'
        iterator = iter(CSVReader(taxa_file_path).read())
        column_names = [x.lower() for x in iterator.next()]
        for columns in iterator:
            row = dict(zip(column_names, columns))
            scientific_name = row['scientific__name']
            piles = row['pile'].lower().split('| ')
            is_in_simple_key = (row['simple_key'] == 'TRUE')
            self.species[scientific_name] = {
                'simple_key': is_in_simple_key,
                'piles': piles
            }
            # Place this plant in the assigned piles.
            for pile in piles:
                if not pile in self.data_set:
                    self.data_set[pile] = {}
                self.data_set[pile][scientific_name] = \
                    self._get_initialized_species(scientific_name,
                                                  is_in_simple_key)

    def _get_piles(self):
        '''Get a list of all the pile names to be checked.'''
        JUNK_PILE_NAMES = ['all', 'unused']
        piles = []
        pile_info_file = self.data_directory_path + '/pile_info.csv'
        iterator = iter(CSVReader(pile_info_file).read())
        column_names = [x.lower() for x in iterator.next()]
        for columns in iterator:
            row = dict(zip(column_names, columns))
            pile_name = row['name'].lower()
            if pile_name in JUNK_PILE_NAMES:
                continue
            piles.append(pile_name)
        return piles

    def _get_data_file_name_mask(self, pile_name):
        '''Tweak the pile name into a mask for finding the data files.'''
        mask = 'pile_' + pile_name.lower().replace('woody ',
            '').replace('aquatic', 'aquatics').replace('-',
            '_').replace(' ', '_') + '*.csv'
        return mask

    def _get_character_data_file_names(self, pile_name):
        '''Get a list of character data file names for a pile.'''
        file_names = []
        mask = self._get_data_file_name_mask(pile_name)
        for file_name in os.listdir(self.data_directory_path):
            if fnmatch.fnmatch(file_name, mask):
                file_names.append(file_name)
        return file_names

    def _add_data_from_file(self, data_file_name, pile):
        '''Add data from a character data file to the coverage data set.'''
        data_file_path = '%s/%s' % (self.data_directory_path, data_file_name)
        iterator = iter(CSVReader(data_file_path).read())
        column_names = [x.lower() for x in iterator.next()]
        for columns in iterator:
            row = dict(zip(column_names, columns))
            # Handle inconsistent column names for the scientific name.
            scientific_name = ''
            if 'scientific__name' in row:
                scientific_name = row['scientific__name']
            else:
                scientific_name = row['scientific_name']
            # Add this species to the pile from the master list if
            # necessary.
            if scientific_name in self.species:
                if scientific_name not in self.data_set[pile]:
                    self.data_set[pile][scientific_name] = \
                        self._get_initialized_species(scientific_name,
                            self.species[scientific_name]['simple_key'])
            else:
                print '    Error: %s not in taxa.csv' % scientific_name
                continue
            # Add the character data keys and values.
            for column_name in column_names:
                # Only column names with pile suffixes are characters.
                if re.search('.*_[a-z]{2}$', column_name):
                    self.data_set[pile][scientific_name]['character_data'] \
                        [column_name] = row[column_name]

    def _add_pile(self, pile):
        ''' Add all the data for a pile.'''
        self.data_set[pile] = {}
        data_file_names = self._get_character_data_file_names(pile)
        for data_file_name in data_file_names:
            self._add_data_from_file(data_file_name, pile)

    def collect(self):
        '''Get all the data needed to report the coverage statistics.'''
        print 'Collecting all species...'
        self._add_all_species()
        piles = self._get_piles()
        for pile in piles:
            print 'Collecting data for %s...' % pile.title()
            self._add_pile(pile)

    def report_on_data(self, simple_key_only=False):
        '''Report coverage for the full data set or just the simple key.'''
        total_species = 0
        total_characters = 0
        total_data_values = 0
        total_filled_in_data_values = 0
        for pile_key, pile_value in self.data_set.iteritems():
            # Get one species so we can count its characters.
            species = next(pile_value.itervalues())
            num_characters = len(species['character_data'])
            total_characters += num_characters
            # Tally the number of species and filled-in data values.
            num_species = 0
            num_filled_in_data_values = 0
            for species in pile_value.itervalues():
                # If we are only checking for the simple key and this
                # species isn't in it, move on.
                if simple_key_only and not species['simple_key']:
                    continue
                num_species += 1
                for character in species['character_data'].keys():
                    if (species['character_data'][character] and
                        len(species['character_data'][character]) > 0):
                        num_filled_in_data_values += 1
            total_species += num_species
            num_data_values = num_species * num_characters
            total_data_values += num_data_values
            total_filled_in_data_values += num_filled_in_data_values
            percent_filled_in = 0.0
            if num_data_values > 0:
                percent_filled_in = float(1.0 * num_filled_in_data_values /
                    num_data_values) * 100
            print ('%s: %.1f%% (%s of %s values; %s species with character '
                   'data; %s characters)') % (pile_key.title(),
                   percent_filled_in,
                   locale.format('%d', num_filled_in_data_values,
                                     grouping=True),
                   locale.format('%d', num_data_values, grouping=True),
                   locale.format('%d', num_species, grouping=True),
                   locale.format('%d', num_characters, grouping=True))
        total_percent_filled_in = float(1.0 * total_filled_in_data_values /
            total_data_values) * 100
        print ('TOTAL: %.1f%% (%s of %s values; %s species with character '
               'data; %s characters)') % (total_percent_filled_in,
                locale.format('%d', total_filled_in_data_values,
                                  grouping=True),
                locale.format('%d', total_data_values, grouping=True),
                locale.format('%d', total_species, grouping=True),
                locale.format('%d', total_characters, grouping=True))

    def report_on_all_species(self):
        '''Report on all the species data collected from taxa.csv, for
           checking consistency.'''
        print 'Number of species loaded from taxa.csv: %s' % \
            locale.format('%d', len(self.species), grouping=True)
        # Because the number of species in taxa.csv has come up larger
        # than the total for the piles, go through the taxa.csv list and
        # report on any species that do not appear in any of the pile
        # character data files.
        plants_without_character_data = []
        for taxon_key, taxon_value in self.species.iteritems():
            taxon_found = False
            for pile_key, pile_value in self.data_set.iteritems():
                if taxon_key in self.data_set[pile_key]:
                    taxon_found = True
                    break
            if not taxon_found:
                plants_without_character_data.append(taxon_key)
        print 'Number of species that do not have any character data: %s' % \
            locale.format('%d', len(plants_without_character_data),
                          grouping=True),
        print '(%s)' % \
            ', '.join([x for x in sorted(plants_without_character_data)])

    def report(self):
        '''Using data already collected, report the coverage statistics.'''
        print '\nFULL DATA SET\n'
        self.report_on_data(simple_key_only=False)
        print '\nSIMPLE KEY\n'
        self.report_on_data(simple_key_only=True)
        print '\nSPECIES LISTED IN TAXA.CSV\n'
        self.report_on_all_species()
        print


def main():
    if len(sys.argv) > 1:
        data_directory_path = sys.argv[1]
        coverage_checker = DataCoverageChecker(data_directory_path)
        coverage_checker.collect()
        coverage_checker.report()
    else:
        print 'Usage: python data-coverage.py {/path/to/data/directory}'


if __name__ == '__main__':
    main()


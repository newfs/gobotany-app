import itertools
import sys

from datetime import date
from StringIO import StringIO

from django.test import TestCase

from gobotany.core.models import (Family, Genus, PartnerSite, PartnerSpecies,
                                  Taxon)
from gobotany.core.rebuild import rebuild_plant_of_the_day
from gobotany.plantoftheday.models import PlantOfTheDay


class PlantOfTheDayTestCase(TestCase):
    FAMILY = 'Sapindaceae'
    GENUS = 'Acer'
    PARTNERS = ['gobotany', 'montshire']

    # The initial list of plants to be imported into a fresh database
    # and loaded into the Plant of the Day list. (Here, "ginnala" is
    # initially misspelled and is corrected in a later test import.)
    SIMPLEKEY_PLANTS = {
        'gobotany': ['negundo', 'pensylvanicum', 'platanoides', 'rubrum',
                     'saccharinum', 'saccharum'],
        'montshire': ['ginala', 'negundo', 'rubrum', 'saccharum']
    }
    NON_SIMPLEKEY_PLANTS = {
        'gobotany': ['campestre', 'ginala', 'nigrum', 'palmatum',
                     'pseudoplatanus'],
        'montshire': ['campestre', 'nigrum', 'palmatum', 'pseudoplatanus']
    }

    # Updated plant data, to test subsequent imports and reloads:
    UPDATED_SIMPLEKEY_PLANTS = {
        'gobotany': ['negundo', 'pensylvanicum', 'platanoides', 'rubrum',
                     'saccharinum', 'saccharum', 'spicatum'],
        'montshire': ['ginnala', 'negundo', 'rubrum', 'saccharum']
    }
    UPDATED_NON_SIMPLEKEY_PLANTS = {
        'gobotany': ['campestre', 'ginala', 'nigrum', 'palmatum',
                     'pseudoplatanus'],
        'montshire': ['campestre', 'nigrum', 'palmatum', 'pseudoplatanus']
    }

    def _import_plants(self, plants, family, genus, simplekey=True):
        for partner, species in plants.items():
            for epithet in species:
                scientific_name = '%s %s' % (self.GENUS, epithet)
                taxon, created = Taxon.objects.get_or_create(
                    scientific_name=scientific_name, family=family,
                    genus=genus)
                taxon.save()
                partner_site = PartnerSite.objects.get(short_name=partner)
                partner_species, created = (
                    PartnerSpecies.objects.get_or_create(
                        species=taxon, partner=partner_site,
                        simple_key=simplekey))
                partner_species.save()


    def _import_plant_data(self, simplekey_plants, non_simplekey_plants):
        family, created = Family.objects.get_or_create(name=self.FAMILY)
        family.save()
        genus, created = Genus.objects.get_or_create(name=self.GENUS,
            family=family)
        genus.save()
        for partner in self.PARTNERS:
            partner_site, created = PartnerSite.objects.get_or_create(
                short_name=partner)
            partner_site.save()
        self._import_plants(simplekey_plants, family, genus, simplekey=True)
        self._import_plants(non_simplekey_plants, family, genus,
                            simplekey=False)

    def setUp(self):
        self._import_plant_data(self.SIMPLEKEY_PLANTS,
                                self.NON_SIMPLEKEY_PLANTS)

    def _get_expected_taxa_count(self, simplekey_plants,
                                 non_simplekey_plants):
        epithets = list(itertools.chain(
            *[p[1] for p in simplekey_plants.items()]))
        epithets += list(itertools.chain(
            *[p[1] for p in non_simplekey_plants.items()]))
        expected_taxa_count = len(set(epithets))
        return expected_taxa_count

    def test_initial_import_loads_expected_taxa(self):
        expected_taxa_count = self._get_expected_taxa_count(
            self.SIMPLEKEY_PLANTS, self.NON_SIMPLEKEY_PLANTS)
        self.assertEqual(expected_taxa_count, len(Taxon.objects.all()))

    def test_initial_import_loads_expected_gobotany_species(self):
        partner_site = PartnerSite.objects.get(short_name='gobotany')
        gobotany_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=True)
        self.assertEqual(len(self.SIMPLEKEY_PLANTS['gobotany']),
            len(gobotany_simplekey_species))
        gobotany_non_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=False)
        self.assertEqual(len(self.NON_SIMPLEKEY_PLANTS['gobotany']),
            len(gobotany_non_simplekey_species))

    def test_initial_import_loads_expected_montshire_species(self):
        partner_site = PartnerSite.objects.get(short_name='montshire')
        montshire_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=True)
        self.assertEqual(len(self.SIMPLEKEY_PLANTS['montshire']),
            len(montshire_simplekey_species))
        montshire_non_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=False)
        self.assertEqual(len(self.NON_SIMPLEKEY_PLANTS['montshire']),
            len(montshire_non_simplekey_species))

    def _run_rebuild_plant_of_the_day(self, include_plants):
        """Run the rebuild function, redirecting message output to a
        return variable for testing and for quiet test output.
        """
        original_stdout = sys.stdout
        sys.stdout = stdout = StringIO()
        rebuild_plant_of_the_day(include_plants=include_plants)
        sys.stdout = original_stdout
        output = stdout.getvalue()
        return output

    def test_initial_plants_of_the_day_build_prints_expected_messages(self):
        include_args = ['SIMPLEKEY', 'ALL']
        for include_arg in include_args:
            output = self._run_rebuild_plant_of_the_day(include_arg)
            self.assertTrue(output.find(
                'Rebuilding Plant of the Day list (%s)' % include_arg) > -1)
            self.assertTrue(output.find('Partner site: gobotany') > -1)
            self.assertTrue(output.find('Partner site: montshire') > -1)

    def test_initial_plants_of_the_day_build_includes_simplekey_plants(self):
        output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')
        expected_plant_count = (len(self.SIMPLEKEY_PLANTS['gobotany']) +
            len(self.SIMPLEKEY_PLANTS['montshire']))
        self.assertEqual(expected_plant_count,
            len(PlantOfTheDay.objects.all()))

    def test_initial_plants_of_the_day_build_includes_all_plants(self):
        output = self._run_rebuild_plant_of_the_day('ALL')
        expected_plant_count = (len(self.SIMPLEKEY_PLANTS['gobotany']) +
            len(self.SIMPLEKEY_PLANTS['montshire']) +
            len(self.NON_SIMPLEKEY_PLANTS['gobotany']) +
            len(self.NON_SIMPLEKEY_PLANTS['montshire']))
        self.assertEqual(expected_plant_count,
            len(PlantOfTheDay.objects.all()))

    def test_rebuild_plants_of_the_day_retains_data(self):
        initial_output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')
        # Set a Plant of the Day as having been featured today.
        plant_of_the_day = PlantOfTheDay.objects.get(
            scientific_name='Acer negundo', partner_short_name='gobotany')
        plant_of_the_day.last_seen = date.today()
        plant_of_the_day.save()

        rebuild_output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')
        expected_plant_count = (len(self.SIMPLEKEY_PLANTS['gobotany']) +
            len(self.SIMPLEKEY_PLANTS['montshire']))
        self.assertEqual(expected_plant_count,
            len(PlantOfTheDay.objects.all()))

        # After rebuilding, the plant should retain its last seen date.
        plant_of_the_day = PlantOfTheDay.objects.get(
            scientific_name='Acer negundo', partner_short_name='gobotany')
        self.assertEqual(date.today(), plant_of_the_day.last_seen)

    def test_import_and_rebuild_loads_expected_data(self):
        # With initial plant data imported (see setUp), build the Plant
        # of the Day list for the first time.
        output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Import a new set of plant data with some changes.
        self._import_plant_data(self.UPDATED_SIMPLEKEY_PLANTS,
                                self.UPDATED_NON_SIMPLEKEY_PLANTS)

        expected_taxa_count = self._get_expected_taxa_count(
            self.UPDATED_SIMPLEKEY_PLANTS, self.UPDATED_NON_SIMPLEKEY_PLANTS)
        self.assertEqual(expected_taxa_count, len(Taxon.objects.all()))

    def test_import_and_rebuild_adds_plants(self):
        # With initial plant data imported (see setUp), build the Plant
        # of the Day list for the first time.
        initial_output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Import a new set of plant data with some changes.
        self._import_plant_data(self.UPDATED_SIMPLEKEY_PLANTS,
                                self.UPDATED_NON_SIMPLEKEY_PLANTS)

        # Now that plant data have been imported again, rebuild the
        # Plant of the Day list.
        rebuild_output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')

        new_plant = PlantOfTheDay.objects.get(
            scientific_name='Acer spicatum', partner_short_name='gobotany')
        self.assertTrue(new_plant)

    def test_import_and_rebuild_changes_plants(self):
        # With initial plant data imported (see setUp), build the Plant
        # of the Day list for the first time.
        initial_output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Import a new set of plant data with some changes.
        self._import_plant_data(self.UPDATED_SIMPLEKEY_PLANTS,
                                self.UPDATED_NON_SIMPLEKEY_PLANTS)

        # Now that plant data have been imported again, rebuild the
        # Plant of the Day list.
        rebuild_output = self._run_rebuild_plant_of_the_day('SIMPLEKEY')

        new_plant = PlantOfTheDay.objects.get(
            scientific_name='Acer ginnala', partner_short_name='montshire')
        self.assertTrue(new_plant)

        # The old plant record with the misspelled name will still exist,
        # but will be set to be excluded later if picked for Plant of
        # the Day because its Taxon record will no longer exist.
        obsolete_plant = PlantOfTheDay.objects.get(
            scientific_name='Acer ginala', partner_short_name='montshire')
        self.assertTrue(obsolete_plant)

import itertools
import random
import sys

from datetime import date, timedelta
from StringIO import StringIO

from django.test import TestCase

from gobotany.core.models import (Family, Genus, PartnerSite, PartnerSpecies,
                                  Taxon)
from gobotany.core.rebuild import rebuild_plant_of_the_day
from gobotany.plantoftheday.models import PlantOfTheDay

# Test data

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

# Utility methods

def _import_plants(plants, family, genus, simplekey=True):
    for partner, species in plants.items():
        for epithet in species:
            scientific_name = '%s %s' % (GENUS, epithet)
            taxon, created = Taxon.objects.get_or_create(
                scientific_name=scientific_name, family=family, genus=genus)
            taxon.save()
            partner_site = PartnerSite.objects.get(short_name=partner)
            partner_species, created = (PartnerSpecies.objects.get_or_create(
                species=taxon, partner=partner_site, simple_key=simplekey))
            partner_species.save()

def _import_plant_data(simplekey_plants, non_simplekey_plants):
    family, created = Family.objects.get_or_create(name=FAMILY)
    family.save()
    genus, created = Genus.objects.get_or_create(name=GENUS, family=family)
    genus.save()
    for partner in PARTNERS:
        partner_site, created = PartnerSite.objects.get_or_create(
            short_name=partner)
        partner_site.save()
    _import_plants(simplekey_plants, family, genus, simplekey=True)
    _import_plants(non_simplekey_plants, family, genus, simplekey=False)

def _get_expected_taxa_count(simplekey_plants, non_simplekey_plants):
    epithets = list(itertools.chain(
        *[p[1] for p in simplekey_plants.items()]))
    epithets += list(itertools.chain(
        *[p[1] for p in non_simplekey_plants.items()]))
    expected_taxa_count = len(set(epithets))
    return expected_taxa_count

def _run_rebuild_plant_of_the_day(include_plants):
    """Run the rebuild function, redirecting message output to a return
    variable for testing and for quiet test output.
    """
    original_stdout = sys.stdout
    sys.stdout = stdout = StringIO()
    rebuild_plant_of_the_day(include_plants=include_plants)
    sys.stdout = original_stdout
    output = stdout.getvalue()
    return output

# Test classes

class PlantOfTheDayTestCase(TestCase):
    def setUp(self):
        _import_plant_data(SIMPLEKEY_PLANTS, NON_SIMPLEKEY_PLANTS)

    def test_initial_import_loads_expected_taxa(self):
        expected_taxa_count = _get_expected_taxa_count(SIMPLEKEY_PLANTS,
                                                       NON_SIMPLEKEY_PLANTS)
        self.assertEqual(expected_taxa_count, len(Taxon.objects.all()))

    def test_initial_import_loads_expected_gobotany_species(self):
        partner_site = PartnerSite.objects.get(short_name='gobotany')
        gobotany_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=True)
        self.assertEqual(len(SIMPLEKEY_PLANTS['gobotany']),
            len(gobotany_simplekey_species))
        gobotany_non_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=False)
        self.assertEqual(len(NON_SIMPLEKEY_PLANTS['gobotany']),
            len(gobotany_non_simplekey_species))

    def test_initial_import_loads_expected_montshire_species(self):
        partner_site = PartnerSite.objects.get(short_name='montshire')
        montshire_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=True)
        self.assertEqual(len(SIMPLEKEY_PLANTS['montshire']),
            len(montshire_simplekey_species))
        montshire_non_simplekey_species = PartnerSpecies.objects.filter(
            partner=partner_site, simple_key=False)
        self.assertEqual(len(NON_SIMPLEKEY_PLANTS['montshire']),
            len(montshire_non_simplekey_species))

    def test_initial_plants_of_the_day_build_prints_expected_messages(self):
        include_args = ['SIMPLEKEY', 'ALL']
        for include_arg in include_args:
            output = _run_rebuild_plant_of_the_day(include_arg)
            self.assertTrue(output.find(
                'Rebuilding Plant of the Day list (%s)' % include_arg) > -1)
            self.assertTrue(output.find('Partner site: gobotany') > -1)
            self.assertTrue(output.find('Partner site: montshire') > -1)

    def test_initial_plants_of_the_day_build_includes_simplekey_plants(self):
        output = _run_rebuild_plant_of_the_day('SIMPLEKEY')
        expected_plant_count = (len(SIMPLEKEY_PLANTS['gobotany']) +
            len(SIMPLEKEY_PLANTS['montshire']))
        self.assertEqual(expected_plant_count,
            len(PlantOfTheDay.objects.all()))

    def test_initial_plants_of_the_day_build_includes_all_plants(self):
        output = _run_rebuild_plant_of_the_day('ALL')
        expected_plant_count = (len(SIMPLEKEY_PLANTS['gobotany']) +
            len(SIMPLEKEY_PLANTS['montshire']) +
            len(NON_SIMPLEKEY_PLANTS['gobotany']) +
            len(NON_SIMPLEKEY_PLANTS['montshire']))
        self.assertEqual(expected_plant_count,
            len(PlantOfTheDay.objects.all()))

    def test_rebuild_plants_of_the_day_retains_data(self):
        initial_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')
        # Set a Plant of the Day as having been featured today.
        plant_of_the_day = PlantOfTheDay.objects.get(
            scientific_name='Acer negundo', partner_short_name='gobotany')
        plant_of_the_day.last_seen = date.today()
        plant_of_the_day.save()

        rebuild_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')
        expected_plant_count = (len(SIMPLEKEY_PLANTS['gobotany']) +
            len(SIMPLEKEY_PLANTS['montshire']))
        self.assertEqual(expected_plant_count,
            len(PlantOfTheDay.objects.all()))

        # After rebuilding, the plant should retain its last seen date.
        plant_of_the_day = PlantOfTheDay.objects.get(
            scientific_name='Acer negundo', partner_short_name='gobotany')
        self.assertEqual(date.today(), plant_of_the_day.last_seen)

    def test_import_and_rebuild_loads_expected_data(self):
        # With initial plant data imported (see setUp), build the Plant
        # of the Day list for the first time.
        output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Import a new set of plant data with some changes.
        _import_plant_data(UPDATED_SIMPLEKEY_PLANTS,
                           UPDATED_NON_SIMPLEKEY_PLANTS)

        expected_taxa_count = _get_expected_taxa_count(
            UPDATED_SIMPLEKEY_PLANTS, UPDATED_NON_SIMPLEKEY_PLANTS)
        self.assertEqual(expected_taxa_count, len(Taxon.objects.all()))

    def test_import_and_rebuild_adds_plants(self):
        # With initial plant data imported (see setUp), build the Plant
        # of the Day list for the first time.
        initial_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Import a new set of plant data with some changes.
        _import_plant_data(UPDATED_SIMPLEKEY_PLANTS,
                           UPDATED_NON_SIMPLEKEY_PLANTS)

        # Now that plant data have been imported again, rebuild the
        # Plant of the Day list.
        rebuild_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

        new_plant = PlantOfTheDay.objects.get(
            scientific_name='Acer spicatum', partner_short_name='gobotany')
        self.assertTrue(new_plant)

    def test_import_and_rebuild_changes_plants(self):
        # With initial plant data imported (see setUp), build the Plant
        # of the Day list for the first time.
        initial_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Import a new set of plant data with some changes.
        _import_plant_data(UPDATED_SIMPLEKEY_PLANTS,
                           UPDATED_NON_SIMPLEKEY_PLANTS)

        # Now that plant data have been imported again, rebuild the
        # Plant of the Day list.
        rebuild_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

        new_plant = PlantOfTheDay.objects.get(
            scientific_name='Acer ginnala', partner_short_name='montshire')
        self.assertTrue(new_plant)

        # The old plant record with the misspelled name will still exist,
        # but will be set to be excluded later if picked for Plant of
        # the Day because its Taxon record will no longer exist.
        obsolete_plant = PlantOfTheDay.objects.get(
            scientific_name='Acer ginala', partner_short_name='montshire')
        self.assertTrue(obsolete_plant)


class PlantOfTheDayManagerTestCase(TestCase):
    """Test the custom model manager (PlantOfTheDay.get_by_date.[...])"""

    def setUp(self):
        _import_plant_data(SIMPLEKEY_PLANTS, NON_SIMPLEKEY_PLANTS)
        initial_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

    def test_manager_returns_seen_plant(self):
        PARTNER = 'gobotany'
        # Set a Plant of the Day's last seen date.
        p = PlantOfTheDay.objects.filter(partner_short_name=PARTNER,
                                         include=True)[0]
        p.last_seen = date.today()
        p.save()
        # Retrieve the plant and verify its name, partner and last seen date.
        retrieved_plant = PlantOfTheDay.get_by_date.for_day(date.today(),
                                                            PARTNER)
        self.assertEqual(p.scientific_name,
                         retrieved_plant.scientific_name)
        self.assertEqual(PARTNER, p.partner_short_name)
        self.assertEqual(p.last_seen, retrieved_plant.last_seen)

    def test_manager_returns_no_plant_for_future_date(self):
        PARTNER = 'gobotany'
        # Set a Plant of the Day's last seen date.
        p = PlantOfTheDay.objects.filter(partner_short_name=PARTNER,
                                         include=True)[0]
        p.last_seen = date.today()
        p.save()
        # Ask for a future Plant of the Day.
        tomorrow = date.today() + timedelta(days=1)
        retrieved_plant = PlantOfTheDay.get_by_date.for_day(tomorrow,
                                                            PARTNER)
        self.assertEqual(None, retrieved_plant)

    def test_manager_returns_random_unseen_plant_for_today(self):
        PARTNER = 'gobotany'
        # Set a few plants' last seen dates.
        SEEN_SPECIES = ['negundo', 'platanoides']
        for (count, epithet) in enumerate(SEEN_SPECIES, start=1):
            scientific_name = '%s %s' % (GENUS, epithet)
            p = PlantOfTheDay.objects.filter(scientific_name=scientific_name,
                                             partner_short_name=PARTNER,
                                             include=True)[0]
            p.last_seen = date.today() - timedelta(days=count)
            p.save()
        # Ask the manager for today's Plant of the Day. Verify that it
        # is one of the species that hasn't been seen yet, and that its
        # last_seen date is now today's date.
        plant_for_today = PlantOfTheDay.get_by_date.for_day(date.today(),
                                                            PARTNER)
        self.assertTrue(plant_for_today)
        specific_epithet = plant_for_today.scientific_name.split(' ')[1]
        self.assertTrue(len(specific_epithet) > 0)
        self.assertTrue(specific_epithet not in SEEN_SPECIES)
        self.assertEqual(date.today(), plant_for_today.last_seen)

    def test_manager_returns_plant_seen_longest_ago_for_today(self):
        PARTNER = 'gobotany'
        # Simulate the plants having been picked at random in the past.
        plants = list(SIMPLEKEY_PLANTS[PARTNER])
        random.shuffle(plants)
        # Set all the plants' last seen dates so that none are unseen.
        for (count, epithet) in enumerate(plants, start=1):
            scientific_name = '%s %s' % (GENUS, epithet)
            p = PlantOfTheDay.objects.filter(scientific_name=scientific_name,
                                             partner_short_name=PARTNER,
                                             include=True)[0]
            p.last_seen = date.today() - timedelta(days=count)
            p.save()

        # Ask the manager for today's Plant of the Day. Verify that it
        # is the plant that had been previously seen longest ago, and
        # that its last_seen date is now today's date.
        plant_for_today = PlantOfTheDay.get_by_date.for_day(date.today(),
                                                            PARTNER)
        self.assertTrue(plant_for_today)
        specific_epithet = plant_for_today.scientific_name.split(' ')[1]
        self.assertTrue(len(specific_epithet) > 0)
        self.assertEqual(specific_epithet, plants[len(plants) - 1])
        self.assertEqual(date.today(), plant_for_today.last_seen)

    def test_manager_excludes_plant_for_nonexistent_taxon(self):
        # Ensure that if the manager encounters a candidate Plant of the
        # Day that no longer exists as a Taxon in the database, that it
        # excludes that candidate from the Plant of the Day list and
        # then picks another plant.
        PARTNER = 'montshire'

        # With initial plant data imported (see setUp), build the Plant
        # of the Day list for the first time.
        initial_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Import a new set of plant data with some changes.
        _import_plant_data(UPDATED_SIMPLEKEY_PLANTS,
                           UPDATED_NON_SIMPLEKEY_PLANTS)
        incorrect_plant = Taxon.objects.get(scientific_name='Acer ginala')
        self.assertTrue(incorrect_plant)
        incorrect_plant.delete()

        # Now that plant data have been imported again, rebuild the
        # Plant of the Day list.
        rebuild_output = _run_rebuild_plant_of_the_day('SIMPLEKEY')

        # Set some last_seen dates so the manager will pick the old,
        # incorrect plant ('ginala') first.
        seen_plants = ['ginnala', 'negundo', 'rubrum', 'saccharum']
        for (count, epithet) in enumerate(seen_plants, start=1):
            scientific_name = '%s %s' % (GENUS, epithet)
            p = PlantOfTheDay.objects.filter(scientific_name=scientific_name,
                                             partner_short_name=PARTNER,
                                             include=True)[0]
            p.last_seen = date.today() - timedelta(days=count)
            p.save()

        # Ask the manager for today's Plant of the Day. Verify that it
        # is the plant that had been previously seen longest ago, and
        # that its last_seen date is now today's date.
        plant_for_today = PlantOfTheDay.get_by_date.for_day(date.today(),
                                                            PARTNER)
        self.assertTrue(plant_for_today)
        specific_epithet = plant_for_today.scientific_name.split(' ')[1]
        self.assertTrue(len(specific_epithet) > 0)
        self.assertEqual(specific_epithet, seen_plants[len(seen_plants) - 1])
        self.assertEqual(date.today(), plant_for_today.last_seen)

        # Verify that the old, incorrect plant has now been excluded,
        # and that its last_seen date has not been updated.
        excluded_plant = PlantOfTheDay.objects.get(
            scientific_name='Acer ginala')
        self.assertTrue(excluded_plant)
        self.assertEqual(False, excluded_plant.include)
        self.assertEqual(None, excluded_plant.last_seen)

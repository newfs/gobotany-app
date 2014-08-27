from django.test import TestCase

from gobotany.core.models import Distribution, Family, Genus, Synonym, Taxon
from gobotany.mapping.map import (NAMESPACES, Path, Legend,
                                  NewEnglandPlantDistributionMap,
                                  NorthAmericanPlantDistributionMap,
                                  UnitedStatesPlantDistributionMap)

def get_legend_labels(legend):
    return [label_node.text for label_node in legend.svg_map.xpath(
        'svg:text/svg:tspan', namespaces=NAMESPACES)]


class PathTestCase(TestCase):
    def setUp(self):
        dist_map = NewEnglandPlantDistributionMap()
        path_nodes = dist_map.svg_map.findall(
            '{http://www.w3.org/2000/svg}path')
        self.path = Path(path_nodes[0])

    def test_get_style(self):
        self.assertTrue(self.path.get_style().find('fill:#fff') > -1)

    def test_set_style(self):
        NEW_STYLE = 'font-size:14px'
        self.path.set_style(NEW_STYLE)
        self.assertEqual(NEW_STYLE, self.path.get_style())

    def test_color(self):
        FILL_COLOR = '#ff0'
        self.path.color(FILL_COLOR)
        self.assertTrue(
            self.path.get_style().find('fill:%s' % FILL_COLOR) > -1)

    def test_color_with_stroke_color(self):
        FILL_COLOR = '#ff0'
        STROKE_COLOR = '#ccc'
        self.path.color(FILL_COLOR, stroke_color=STROKE_COLOR)
        self.assertTrue(
            self.path.get_style().find('fill:%s' % FILL_COLOR) > -1)
        self.assertTrue(
            self.path.get_style().find('stroke:%s' % STROKE_COLOR) > -1)


class LegendTestCase(TestCase):
    def setUp(self):
        self.dist_map = NewEnglandPlantDistributionMap()
        self.legend = Legend(self.dist_map.svg_map, maximum_categories=2,
            maximum_items=5)

    def test_set_item_label(self):
        LABEL = 'native'
        label_node = self.legend.svg_map.xpath('svg:text',
            namespaces=NAMESPACES)[0]
        self.legend._set_item_label(label_node, LABEL)
        label_text_node = label_node.find('{http://www.w3.org/2000/svg}tspan')
        self.assertEqual(LABEL, label_text_node.text)

    def _get_paths(self):
        return [Path(box_node) for box_node in self.legend.svg_map.xpath(
            'svg:rect', namespaces=NAMESPACES)]

    def test_set_item(self):
        SLOT = 1
        FILL_COLOR = '#ff0'
        STROKE_COLOR = '#ccc'
        LABEL = 'present'
        self.legend._set_item(SLOT, FILL_COLOR, STROKE_COLOR, LABEL)

        labels = get_legend_labels(self.legend)
        self.assertEqual('present', labels[0])

        paths = self._get_paths()
        self.assertTrue(paths[0].get_style().find(
            'fill:%s' % FILL_COLOR) > -1)
        self.assertTrue(paths[0].get_style().find(
            'stroke:%s' % STROKE_COLOR) > -1)

    def test_show_items(self):
        legend_labels_found = ['present na']
        self.legend.show_items(legend_labels_found)

        labels = get_legend_labels(self.legend)
        self.assertEqual('present', labels[0])

        paths = self._get_paths()
        self.assertTrue(paths[0].get_style().find('fill:#35880c') > -1)
        self.assertTrue(paths[1].get_style().find('fill:#fff') > -1)
        [self.assertTrue(path.get_style().find('fill:#fff') > -1)
         for path in paths[2:]]
        [self.assertTrue(path.get_style().find('stroke:#fff') > -1)
         for path in paths[0:2]]
        [self.assertTrue(path.get_style().find('stroke:#fff') > -1)
         for path in paths[2:]]


class ChloroplethMapTestCase(TestCase):
    def setUp(self):
        self.chloropleth_map = NewEnglandPlantDistributionMap()

    def test_get_title(self):
        self.assertEqual('New England Distribution Map',
                         self.chloropleth_map.get_title())

    def test_set_title(self):
        TITLE = 'Test'
        self.chloropleth_map.set_title(TITLE)
        self.assertEqual(TITLE, self.chloropleth_map.get_title())

    def test_tostring(self):
        self.assertEqual(u'<svg xmlns', self.chloropleth_map.tostring()[0:10])


def create_distribution_records():
    """Create dummy distribution records for New England and beyond."""
    taxa = {'Dendrolycopodium dendroideum': 'Lycopodiaceae',
            'Vaccinium vitis-idaea': 'Ericaceae'}
    for scientific_name, family_name in taxa.items():
        family = Family(name=family_name)
        family.save()
        genus = Genus(name=scientific_name.split(' ')[0], family=family)
        genus.save()
        taxon = Taxon(scientific_name=scientific_name, family=family,
                      genus=genus)
        taxon.save()

    taxon = Taxon.objects.get(scientific_name='Vaccinium vitis-idaea')
    synonym = Synonym(scientific_name='Vaccinium vitis-idaea ssp. minus',
            full_name='Vaccinium vitis-idaea ssp. minus (Lodd.) Hulten',
            taxon=taxon)
    synonym.save()

    # The county (or district) and state will not usually be lowercase,
    # but the code is case-insensitive to make both the map and data
    # more resilient.
    #
    # Currently, North America distribution data is at the state,
    # province, or territory level. These records will be present
    # alongside the New England records.
    #
    # format: county, state, present, native
    distribution_data = {
        'Dendrolycopodium dendroideum': [
            ('Piscataquis', 'ME', True, True),
            ('Coos', 'NH', True, True),
            ('Worcester', 'MA', True, True),
            ('Kent', 'RI', True, True),
            ('Orange', 'VT', True, True),
            ('New London', 'CT', True, True),
            ('', 'NS', True, True),
            ('', 'NB', True, True),
            ('', 'QC', True, True),
            ('', 'ON', True, True),
            ('', 'MB', True, True),
            ('', 'SK', True, True),
            ('', 'AB', True, True),
            ('', 'BC', True, True),
            ('', 'ME', True, True),
            ('', 'NH', True, True),
            ('', 'MA', True, True),
            ('', 'RI', True, True),
            ('', 'VT', True, True),
            ('', 'CT', True, True),
            ('', 'NY', True, True),
            ('', 'nj', True, True),
            ('', 'PA', True, True),
            ('', 'NC', True, True),
            ],
        'Vaccinium vitis-idaea ssp. minus': [
            ('Pistcataquis', 'ME', True, True),
            ('Coos', 'NH', True, True),
            ('Worcester', 'MA', True, True),
            ('Kent', 'RI', True, True),
            ('Orange', 'VT', True, True),
            ('New London', 'CT', True, True),
            ('', 'NS', True, True),
            ('', 'NB', True, True),
            ('', 'QC', True, True),
            ('', 'ON', True, True),
            ('', 'MB', True, True),
            ('', 'SK', True, True),
            ('', 'AB', True, True),
            ('', 'BC', True, True),
            ('', 'ME', True, True),
            ('', 'NH', True, True),
            ('', 'MA', True, True),
            ('', 'RI', True, True),
            ('', 'VT', True, True),
            ('', 'CT', False, False),
            ('', 'NY', False, False),
            ('', 'NJ', False, False),
            ('', 'pa', False, False),
            ],
        'Sambucus nigra': [
            ('', 'CT', True, False),
            ('Fairfield', 'CT', False, False),
            ('Hartford', 'CT', False, False),
            ('Litchfield', 'CT', False, False),
            ('Middlesex', 'CT', False, False),
            ('New Haven', 'CT', False, False),
            ('New London', 'CT', False, False),
            ('Tolland', 'CT', False, False),
            ('Windham', 'CT', False, False),
            ],
        'Sambucus nigra ssp. canadensis': [
            ('', 'CT', True, True),
            ('Fairfield', 'CT', True, True),
            ('Hartford', 'CT', True, True),
            ('Litchfield', 'CT', True, True),
            ('Middlesex', 'CT', True, True),
            ('New Haven', 'CT', True, True),
            ('New London', 'CT', True, True),
            ('Tolland', 'CT', True, True),
            ('Windham', 'CT', True, True),
            ],
        'Sambucus nigra ssp. nigra': [
            ('', 'CT', True, False),
            ('Fairfield', 'CT', False, False),
            ('Hartford', 'CT', False, False),
            ('Litchfield', 'CT', False, False),
            ('Middlesex', 'CT', False, False),
            ('New Haven', 'CT', False, False),
            ('New London', 'CT', False, False),
            ('Tolland', 'CT', False, False),
            ('Windham', 'CT', False, False),
            ],
        'Leptochloa fusca': [
            ('', 'MA', True, False),
            ('Middlesex', 'MA', True, False),
            ],
        'Leptochloa fusca ssp. fascicularis': [
            ('', 'CT', True, False),
            ('Fairfield', 'CT', True, True),
            ('New Haven', 'CT', True, True),
            ('New London', 'CT', True, True),
            ('', 'MA', True, False),
            ('Barnstable', 'MA', True, True),
            ('Dukes', 'MA', True, True),
            ('Franklin', 'MA', True, True),
            ('Middlesex', 'MA', True, True),
            ('Nantucket', 'MA', True, True),
            ('Suffolk', 'MA', True, True),
            ('Worcester', 'MA', True, True),
            ('', 'ME', True, False),
            ('', 'NH', True, False),
            ('Rockingham', 'NH', True, True),
            ('', 'RI', True, False),
            ('Newport', 'RI', True, True),
            ('Washington', 'RI', True, True),
            ('', 'VT', True, False),
            ('Chittenden', 'VT', True, True),
            ],
        'Leptochloa fusca ssp. uninervia': [
            ('', 'MA', True, False),
            ('Middlesex', 'MA', True, False),
            ],
        }
    for scientific_name, data_list in distribution_data.items():
        for entry in data_list:
            distribution = Distribution(scientific_name=scientific_name,
                county=entry[0], state=entry[1], present=entry[2],
                native=entry[3])
            distribution.save()


class PlantDistributionMapTestCase(TestCase):
    def setUp(self):
        self.distribution_map = NewEnglandPlantDistributionMap()
        create_distribution_records()

    def test_map_init(self):
        self.assertTrue(self.distribution_map)

    def test_get_label_absent(self):
        self.assertEqual('absent',
            self.distribution_map._get_label(False, False))

    def test_get_label_native(self):
        self.assertEqual('native',
            self.distribution_map._get_label(True, True))

    def test_get_label_non_native(self):
        self.assertEqual('non-native',
            self.distribution_map._get_label(True, False))

    def test_add_name_to_title(self):
        SCIENTIFIC_NAME = 'Tsuga canadensis'
        self.distribution_map._add_name_to_title(SCIENTIFIC_NAME)
        self.assertEqual('%s: New England Distribution Map' % SCIENTIFIC_NAME,
                         self.distribution_map.get_title())

    def test_get_distribution_records(self):
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        records = (self.distribution_map._get_distribution_records(
                   SCIENTIFIC_NAME))
        self.assertTrue(len(records) > 0)

    def test_set_plant(self):
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.assertEqual(SCIENTIFIC_NAME,
                         self.distribution_map.scientific_name)
        self.assertEqual('%s: New England Distribution Map' % SCIENTIFIC_NAME,
                         self.distribution_map.get_title())
        self.assertTrue(len(self.distribution_map.distribution_records) > 0)

    def _check_equal(self, list1, list2):
        return list1[1:] == list2[:-1]

    def _verify_shaded_counties(self, legend_labels_found):
        path_nodes = self.distribution_map.svg_map.findall(
            '{http://www.w3.org/2000/svg}path')
        paths = [Path(path_node) for path_node in path_nodes]
        statuses_verified = []
        for path in paths:
            style = path.get_style()
            status = None
            if style.find('fill:#78bf47') > -1:
                status = 'native'
            elif style.find('fill:#fff') > -1:
                status = 'absent'
            if status and status not in statuses_verified:
                statuses_verified.append(status)
            if statuses_verified == legend_labels_found:
                break
        self.assertEqual(statuses_verified.sort(), legend_labels_found.sort())

    def test_shade_counties(self):
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        legend_labels_found = self.distribution_map._shade_areas()
        self._verify_shaded_counties(legend_labels_found)

    def test_shade(self):
        SCIENTIFIC_NAME = 'Vaccinium vitis-idaea ssp. minus'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.distribution_map.shade()
        self._verify_shaded_counties(['native', 'absent'])
        labels = get_legend_labels(self.distribution_map.legend)
        self.assertEqual('present', labels[0])
        self.assertEqual('undocumented', labels[1])

    def test_plant_with_distribution_data_has_plant_name_in_title(self):
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.distribution_map.shade()
        self.assertEqual('%s: New England Distribution Map' % SCIENTIFIC_NAME,
                         self.distribution_map.get_title())

    def test_plant_with_no_distribution_data_returns_blank_map(self):
        SCIENTIFIC_NAME = 'Foo bar'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.distribution_map.shade()
        # Verify that the map is not shaded.
        path_nodes = self.distribution_map.svg_map.findall(
            '{http://www.w3.org/2000/svg}path')
        paths = [Path(path_node) for path_node in path_nodes]
        for path in paths:
            style = path.get_style()
            self.assertTrue(style.find('fill:#fff') > -1 or
                            style.find('fill:none') > -1)
        # Verify that the legend contains only a 'no data' label.
        labels = get_legend_labels(self.distribution_map.legend)
        self.assertEqual(['no data', '', '', '', '', ''], labels)

    def test_plant_with_no_distribution_data_has_no_plant_name_in_title(self):
        SCIENTIFIC_NAME = 'Foo bar'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.distribution_map.shade()
        self.assertEqual('New England Distribution Map',
                         self.distribution_map.get_title())

    def test_plant_with_data_only_under_synonym_returns_shaded_map(self):
        # This plant's distribution data is listed only under the
        # synonym Vaccinium vitis-idaea ssp. minus.
        SCIENTIFIC_NAME = 'Vaccinium vitis-idaea'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.distribution_map.shade()
        self._verify_shaded_counties(['present', 'absent'])
        labels = get_legend_labels(self.distribution_map.legend)
        self.assertEqual(['present', 'undocumented', '', '', 'Native', ''],
            labels)
        self.assertEqual('%s: New England Distribution Map' % SCIENTIFIC_NAME,
                         self.distribution_map.get_title())

    def test_legend_correct_with_conflicting_state_and_county_records(self):
        # Ensure that if all of a plant's county-level records override
        # its state-level record, that the map legend lists only those
        # items that are visible on the final map.
        SCIENTIFIC_NAME = 'Sambucus nigra'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.distribution_map.shade()
        labels = get_legend_labels(self.distribution_map.legend)
        legend_shows_non_native = ('non-native' in labels)
        self.assertFalse(legend_shows_non_native)

    def test_species_and_infraspecific_taxa_shaded_together(self):
        # Ensure that the distribution records for a species and any
        # associated infraspecific taxa are shaded together on the map,
        # with native overriding non-native.
        SCIENTIFIC_NAME = 'Sambucus nigra'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        self.distribution_map.shade()
        labels = get_legend_labels(self.distribution_map.legend)
        legend_shows_native = ('native, st.' or 'native, co.' in labels)
        self.assertTrue(legend_shows_native)


class NewEnglandPlantDistributionMapTestCase(TestCase):
    def setUp(self):
        self.distribution_map = NewEnglandPlantDistributionMap()
        create_distribution_records()

    def test_is_correct_map(self):
        self.assertEqual('New England Distribution Map',
                         self.distribution_map.get_title())

    def test_get_distribution_records(self):
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        records = (self.distribution_map._get_distribution_records(
                   SCIENTIFIC_NAME))
        self.assertTrue(len(records) > 0)


class UnitedStatesPlantDistributionMapTestCase(TestCase):
    def setUp(self):
        self.distribution_map = UnitedStatesPlantDistributionMap()

    def test_is_correct_map(self):
        self.assertEqual('United States Distribution Map',
                         self.distribution_map.get_title())


class NorthAmericanPlantDistributionMapTestCase(TestCase):
    def setUp(self):
        self.distribution_map = NorthAmericanPlantDistributionMap()
        create_distribution_records()

    def _get_shaded_paths(self, distribution_map):
        path_nodes = distribution_map.svg_map.xpath(
            'svg:g/svg:path', namespaces=NAMESPACES)
        paths = [Path(path_node) for path_node in path_nodes]
        shaded_paths = []
        for path in paths:
            style = path.get_style()
            if style.find('fill:#') > -1 and style.find('fill:#fff') == -1:
                shaded_paths.append(path)
        return shaded_paths

    def _verify_number_expected_shaded_areas(self, expected_shaded_areas,
            shaded_paths):
        # Verify that the number of expected shaded areas is found, at a
        # minimum, among the full list of shaded paths.
        # There can be more shaded paths than expected shaded areas.
        # Example: BC has two paths, one for the mainland and one for
        # Vancouver Island.
        #
        # To debug a failing test, uncomment the following line and run
        # the failing test alone:
        #print 'shaded_paths: %d  expected_shaded_areas: %d' % (
        #    len(shaded_paths), len(expected_shaded_areas))
        self.assertTrue(len(shaded_paths) >= len(expected_shaded_areas))

    def _verify_expected_shaded_areas(self, expected_shaded_areas,
            shaded_paths):
        # Check that each shaded area and its color is expected.
        for path in shaded_paths:
            path_id = path.path_node.get('id')
            area_key = path_id[0:2]
            self.assertTrue(area_key in expected_shaded_areas.keys())
            label = expected_shaded_areas[area_key]
            # To debug a failing test, uncomment the following line and
            # run the failing test alone:
            #print 'area_key: %s  label: %s' % (area_key, label)
            fill_declaration = 'fill:%s' % Legend.COLORS[label]
            self.assertTrue(path.get_style().find(fill_declaration) > -1)

    def test_is_correct_map(self):
        self.assertEqual('North American Distribution Map',
                         self.distribution_map.get_title())

    def test_distribution_areas_are_shaded_correctly(self):
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        # Currently, data for North America are only available at the
        # state, province, and territory level.
        EXPECTED_SHADED_AREAS = {
            'CT': 'native',
            'MA': 'native',
            'ME': 'native',
            'NH': 'native',
            'NJ': 'native',
            'NY': 'native',
            'PA': 'native',
            'NC': 'native',
            'RI': 'native',
            'VT': 'native',
            'NS': 'native',
            'NB': 'native',
            'QC': 'native',
            'ON': 'native',
            'MB': 'native',
            'SK': 'native',
            'AB': 'native',
            'BC': 'native',
            }
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        records = (self.distribution_map._get_distribution_records(
                   SCIENTIFIC_NAME))
        self.assertTrue(len(records) > 0)
        self.distribution_map.shade()
        shaded_paths = self._get_shaded_paths(self.distribution_map)
        self._verify_number_expected_shaded_areas(EXPECTED_SHADED_AREAS,
            shaded_paths)
        self._verify_expected_shaded_areas(EXPECTED_SHADED_AREAS,
            shaded_paths)

    def test_county_level_native_overrides_state_level_non_native(self):
        # Ensure that if a plant is marked non-native at the state
        # level, but native in one or more counties, that the state is
        # then overridden to be shaded as native on the map.
        SCIENTIFIC_NAME = 'Leptochloa fusca'
        EXPECTED_SHADED_AREAS = {
            'CT': 'native',
            'MA': 'native',
            'ME': 'non-native',
            'NH': 'native',
            'RI': 'native',
            'VT': 'native',
        }
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        records = (self.distribution_map._get_distribution_records(
                   SCIENTIFIC_NAME))
        self.assertTrue(len(records) > 0)
        self.distribution_map.shade()
        shaded_paths = self._get_shaded_paths(self.distribution_map)
        self._verify_number_expected_shaded_areas(EXPECTED_SHADED_AREAS,
            shaded_paths)
        self._verify_expected_shaded_areas(EXPECTED_SHADED_AREAS,
            shaded_paths)

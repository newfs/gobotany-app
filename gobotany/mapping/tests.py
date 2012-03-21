from django.test import TestCase

from gobotany.core.models import Distribution, Family, Genus, Synonym, Taxon
from gobotany.mapping.map import (NAMESPACES, Path, Legend,
                                  NewEnglandPlantDistributionMap,
                                  NorthAmericanPlantDistributionMap,
                                  UnitedStatesPlantDistributionMap)

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
        self.legend = Legend(self.dist_map.svg_map, maximum_items=5)

    def test_set_item_label(self):
        LABEL = 'native'
        label_node = self.legend.svg_map.xpath('svg:text',
            namespaces=NAMESPACES)[0]
        self.legend._set_item_label(label_node, LABEL)
        label_text_node = label_node.find('{http://www.w3.org/2000/svg}tspan')
        self.assertEqual(LABEL, label_text_node.text)

    def _get_labels(self):
        return [label_node.text for label_node in self.legend.svg_map.xpath(
            'svg:text/svg:tspan', namespaces=NAMESPACES)]

    def _get_paths(self):
        return [Path(box_node) for box_node in self.legend.svg_map.xpath(
            'svg:rect', namespaces=NAMESPACES)]

    def test_set_item(self):
        SLOT = 1
        FILL_COLOR = '#ff0'
        STROKE_COLOR = '#ccc'
        LABEL = 'native'
        self.legend._set_item(SLOT, FILL_COLOR, STROKE_COLOR, LABEL)

        labels = self._get_labels()
        self.assertEqual('native', labels[0])

        paths = self._get_paths()
        self.assertTrue(paths[0].get_style().find(
            'fill:%s' % FILL_COLOR) > -1)
        self.assertTrue(paths[0].get_style().find(
            'stroke:%s' % STROKE_COLOR) > -1)

    def test_show_items(self):
        legend_labels_found = ['native', 'rare']
        self.legend.show_items(legend_labels_found)

        labels = self._get_labels()
        self.assertEqual('native', labels[0])
        self.assertEqual('rare', labels[1])
        [self.assertEqual('', label) for label in labels[2:]]

        paths = self._get_paths()
        self.assertTrue(paths[0].get_style().find('fill:#78bf47') > -1)
        self.assertTrue(paths[1].get_style().find('fill:#a7e37d') > -1)
        [self.assertTrue(path.get_style().find('fill:#fff') > -1)
         for path in paths[2:]]
        [self.assertTrue(path.get_style().find('stroke:#000') > -1)
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
    distribution_data = {
        'Dendrolycopodium dendroideum': [
            ('Piscataquis', 'ME', 'Species present and not rare'),
            ('Coos', 'NH', 'Species present and not rare'),
            ('Worcester', 'MA', 'Species present and not rare'),
            ('Kent', 'RI', 'Species present in state and native'),
            ('Orange', 'VT', 'Species present and not rare'),
            ('New London', 'CT', 'Species present in state and native'),
            ('', 'NS', 'Species present in state and native'),
            ('', 'NB', 'Species present in state and native'),
            ('', 'QC', 'Species present in state and native'),
            ('', 'ON', 'Species present in state and native'),
            ('', 'MB', 'Species present in state and native'),
            ('', 'SK', 'Species present in state and native'),
            ('', 'AB', 'Species present in state and native'),
            ('', 'BC', 'Species present in state and native'),
            ('', 'ME', 'Species present in state and native'),
            ('', 'NH', 'Species present in state and native'),
            ('', 'MA', 'Species present in state and native'),
            ('', 'RI', 'Species present in state and native'),
            ('', 'VT', 'Species present in state and native'),
            ('', 'CT', 'Species present in state and native'),
            ('', 'NY', 'Species present in state and native'),
            ('', 'nj', 'Species present in state and native'),
            ('', 'PA', 'Species present in state and native'),
            ('', 'NC', 'Species present and rare'),
            ],
        'Vaccinium vitis-idaea ssp. minus': [
            ('Pistcataquis', 'ME', 'Species present and not rare'),
            ('Coos', 'NH', 'Species present and not rare'),
            ('Worcester', 'MA', 'Species present and rare'),
            ('Kent', 'RI', 'Species not present in state'),
            ('Orange', 'VT', 'Species present in state and native'),
            ('New London', 'CT', 'Species present in state and native'),
            ('', 'NS', 'Species present in state and native'),
            ('', 'NB', 'Species present in state and native'),
            ('', 'QC', 'Species present in state and native'),
            ('', 'ON', 'Species present in state and native'),
            ('', 'MB', 'Species present in state and native'),
            ('', 'SK', 'Species present in state and native'),
            ('', 'AB', 'Species present in state and native'),
            ('', 'BC', 'Species present in state and native'),
            ('', 'ME', 'Species present in state and native'),
            ('', 'NH', 'Species present in state and native'),
            ('', 'MA', 'Species present and rare'),
            ('', 'RI', 'Species not present in state'),
            ('', 'VT', 'Species present and rare'),
            ('', 'CT', 'Species extirpated (historic)'),
            ('', 'NY', 'Species not present in state'),
            ('', 'NJ', 'Species not present in state'),
            ('', 'pa', 'Species not present in state')
            ]
        }
    for scientific_name, data_list in distribution_data.items():
        for entry in data_list:
            distribution = Distribution(scientific_name=scientific_name,
                county=entry[0], state=entry[1], status=entry[2])
            distribution.save()


class PlantDistributionMapTestCase(TestCase):
    def setUp(self):
        self.distribution_map = NewEnglandPlantDistributionMap()
        create_distribution_records()

    def test_map_init(self):
        self.assertTrue(self.distribution_map)

    def test_get_label_for_status_native(self):
        statuses = [
            'Species present in state and native',
            'Species present and not rare',
            'Species native, but adventive in state',
            ]
        for status in statuses:
            self.assertEqual('native',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_rare(self):
        statuses = [
            'Species present and rare',
            ]
        for status in statuses:
            self.assertEqual('rare',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_introduced(self):
        statuses = [
            'Species present in state and exotic',
            'Species exotic and present',
            'Species waif',
            ]
        for status in statuses:
            self.assertEqual('introduced',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_invasive(self):
        statuses = [
            'Species noxious',
            ]
        for status in statuses:
            self.assertEqual('invasive',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_historic(self):
        statuses = [
            'Species extirpated (historic)',
            'Species extinct',
            ]
        for status in statuses:
            self.assertEqual('historic',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_absent(self):
        statuses = [
            'Species not present in state',
            'Species eradicated',
            'Questionable Presence (cross-hatched)',
            ]
        for status in statuses:
            self.assertEqual('absent',
                self.distribution_map._get_label_for_status(status))

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
            elif style.find('fill:#a7e37d') > -1:
                status = 'rare'
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
        self._verify_shaded_counties(['native', 'rare', 'absent'])
        labels = [label_node.text for label_node in
            self.distribution_map.legend.svg_map.xpath('svg:text/svg:tspan',
            namespaces=NAMESPACES)]
        self.assertEqual('native', labels[0])
        self.assertEqual('rare', labels[1])
        self.assertEqual('absent', labels[2])
        [self.assertEqual('', label) for label in labels[3:]]

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
        labels = [label_node.text for label_node in
            self.distribution_map.legend.svg_map.xpath('svg:text/svg:tspan',
            namespaces=NAMESPACES)]
        self.assertEqual(['no data', '', '', '', ''], labels)

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
        self._verify_shaded_counties(['native', 'rare', 'absent'])
        labels = [label_node.text for label_node in
            self.distribution_map.legend.svg_map.xpath('svg:text/svg:tspan',
            namespaces=NAMESPACES)]
        self.assertEqual(['native', 'rare', 'absent', '', ''], labels)
        self.assertEqual('%s: New England Distribution Map' % SCIENTIFIC_NAME,
                         self.distribution_map.get_title())


class NewEnglandPlantDistributionMapTestCase(TestCase):
    def setUp(self):
        self.distribution_map = NewEnglandPlantDistributionMap()
        create_distribution_records()

    def test_is_correct_map(self):
        self.assertEqual('New England Distribution Map',
                         self.distribution_map.get_title())

    def test_get_distribution_records(self):
        NEW_ENGLAND_STATES = ['CT', 'MA', 'ME', 'NH', 'RI', 'VT']
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        records = (self.distribution_map._get_distribution_records(
                   SCIENTIFIC_NAME))
        self.assertTrue(len(records) > 0)
        [self.assertTrue(record.state in NEW_ENGLAND_STATES)
         for record in records]


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

    def test_is_correct_map(self):
        self.assertEqual('North American Distribution Map',
                         self.distribution_map.get_title())

    def test_distribution_areas_are_shaded_correctly(self):
        SCIENTIFIC_NAME = 'Dendrolycopodium dendroideum'
        COLORS = Legend.COLORS
        # Currently, data for North America are only available at the
        # state, province, and territory level.
        EXPECTED_SHADED_AREAS = {
            'CT': COLORS['native'],
            'MA': COLORS['native'],
            'ME': COLORS['native'],
            'NH': COLORS['native'],
            'NJ': COLORS['native'],
            'NY': COLORS['native'],
            'PA': COLORS['native'],
            'NC': COLORS['rare'],
            'RI': COLORS['native'],
            'VT': COLORS['native'],
            'NS': COLORS['native'],
            'NB': COLORS['native'],
            'QC': COLORS['native'],
            'ON': COLORS['native'],
            'MB': COLORS['native'],
            'SK': COLORS['native'],
            'AB': COLORS['native'],
            'BC': COLORS['native'],
            }
        self.distribution_map.set_plant(SCIENTIFIC_NAME)
        records = (self.distribution_map._get_distribution_records(
                   SCIENTIFIC_NAME))
        self.assertTrue(len(records) > 0)
        self.distribution_map.shade()
        path_nodes = self.distribution_map.svg_map.xpath(
            'svg:g/svg:path', namespaces=NAMESPACES)
        paths = [Path(path_node) for path_node in path_nodes]
        shaded_paths = []
        for path in paths:
            style = path.get_style()
            if style.find('fill:#') > -1 and style.find('fill:#fff') == -1:
                shaded_paths.append(path)
        # There can be more shaded paths than expected shaded areas.
        # Example: BC has two paths, one for the mainland and one for
        # Vancouver Island.
        self.assertTrue(len(shaded_paths) >= len(EXPECTED_SHADED_AREAS))
        # Check that each shaded area and its color is expected.
        for path in shaded_paths:
            path_id = path.path_node.get('id')
            area_key = path_id[0:2]
            self.assertTrue(area_key in EXPECTED_SHADED_AREAS.keys())
            expected_color = EXPECTED_SHADED_AREAS[area_key]
            fill_declaration = 'fill:%s' % expected_color
            self.assertTrue(path.get_style().find(fill_declaration) > -1)


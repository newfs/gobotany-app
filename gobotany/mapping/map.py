import re
from os.path import abspath, dirname
from django.core.exceptions import ObjectDoesNotExist
from lxml import etree
from gobotany.core import models

GRAPHICS_ROOT = abspath(dirname(__file__) + '/../static/graphics')
NAMESPACES = {'svg': 'http://www.w3.org/2000/svg'}

class Path(object):
    """Class for operating on a SVG path node."""
    STYLE_ATTR = 'style'
    FILL_PATTERN = re.compile(r'(.*fill:)#[a-f0-9]{3,6}(;.*|$)')
    STROKE_PATTERN = re.compile(r'(.*stroke:)#[a-f0-9]{3,6}(;.*|$)')

    def __init__(self, path_node):
        self.path_node = path_node

    def get_style(self):
        return self.path_node.get(Path.STYLE_ATTR)

    def set_style(self, value):
        self.path_node.set(Path.STYLE_ATTR, value)

    def color(self, fill_color, stroke_color=None):
        style = self.get_style()
        replacement = r'\1%s\2' % fill_color
        shaded_style = re.sub(Path.FILL_PATTERN, replacement, style)
        if stroke_color:
            replacement = r'\1%s\2' % stroke_color
            shaded_style = re.sub(Path.STROKE_PATTERN, replacement,
                                  shaded_style)
        self.set_style(shaded_style)

    def __str__(self):
        return '%s (%s)' % (self.path_node.get('id'), self.get_style())


class Legend(object):
    """Class for configuring the legend on a SVG plant distribution map."""

    # This list controls the order, label and color of legend items.
    #
    # Some of the items are currently no longer shown on the maps, due
    # to simpler and more accurate data in use. These items are left
    # here in case it is desired to make the maps more elaborate again.
    ITEMS = [('native', '#78bf47'),
             ('non-native', '#fa9691'),
             ('absent', '#fff'),
             #('rare', '#a7e37d'),       # Currently not shown on the maps.
             #('invasive', '#f00'),      # Currently not shown on the maps.
             #('historic', '#ccc'),      # Currently not shown on the maps.
             ]
    COLORS = dict(ITEMS)  # Color lookup for labels, ex.: COLORS['rare'].
                          # This does not preserve the order of items.

    def __init__(self, svg_map, maximum_items):
        self.svg_map = svg_map
        self.maximum_items = maximum_items

    def _set_item_label(self, label_node, label):
        label_text_node = label_node.find('{http://www.w3.org/2000/svg}tspan')
        label_text_node.text = label

    def _set_item(self, slot_number, fill_color, stroke_color, item_label):
        box_node_id = 'box%s' % str(slot_number)
        box_node = self.svg_map.xpath('svg:rect[@id="%s"]' % box_node_id,
            namespaces=NAMESPACES)[0]
        box = Path(box_node)
        box.color(fill_color, stroke_color)

        label_node_id = 'label%s' % str(slot_number)
        label_node = self.svg_map.xpath('svg:text[@id="%s"]' % label_node_id,
            namespaces=NAMESPACES)[0]
        self._set_item_label(label_node, item_label)

    def show_items(self, legend_labels_found):
        """Set the colors and labels of the legend items."""
        for item_slot_number in range(1, self.maximum_items + 1):
            # Only show legend items for data values shown on this map.
            if len(legend_labels_found) >= item_slot_number:
                # Show the legend item.
                label = legend_labels_found[item_slot_number - 1]
                fill_color = Legend.COLORS[label]
                stroke_color = '#000'
            else:
                # Do not show the legend item, and hide its box.
                label = ''
                fill_color = '#fff'
                stroke_color = '#fff'
            self._set_item(item_slot_number, fill_color, stroke_color, label)

        # If no distribution data were mapped, set a label saying so.
        if len(legend_labels_found) == 0:
            self._set_item(1, '#fff', '#fff', 'no data')


class ChloroplethMap(object):
    """Base class for a chloropleth SVG map."""

    def __init__(self, blank_map_path, maximum_legend_items):
        self.svg_map = etree.parse(blank_map_path)
        self.maximum_legend_items = maximum_legend_items

    def _get_title_node(self):
        return self.svg_map.find('{http://www.w3.org/2000/svg}title')

    def get_title(self):
        title = self._get_title_node()
        return title.text

    def set_title(self, value):
        title = self._get_title_node()
        title.text = value

    def tostring(self):
        return etree.tostring(self.svg_map.getroot())


class PlantDistributionMap(ChloroplethMap):
    """Base class for a map that shows plant distribution data."""

    PATH_NODES_XPATH = 'svg:path'

    def __init__(self, blank_map_path):
        self.maximum_legend_items = 5
        self.scientific_name = None
        super(PlantDistributionMap, self).__init__(blank_map_path,
            self.maximum_legend_items)
        self.legend = Legend(self.svg_map, self.maximum_legend_items)

    def _get_label_for_status(self, status):
        """Return the appropriate label for a distribution status string.

        Because the Go Botany maps are aimed at a general audience, the
        Go Botany map labels are fewer and simpler than those found on
        the source maps.

        23 May 2012: Labels are down to just present and absent due to
        the use of simpler and more accurate New England data. The
        labels for North America data are now made to "match" the New
        England ones, so the maps will be consistent.
        """
        ABSENCE_INDICATORS = [
                'absent',       # From adjusted New England data, covers
                                # "absent"
                'extirpated',   # Covers: "Species extirpated (historic)"
                'extinct',      # Covers: "Species extinct"
                'not present',  # Covers: "Species not present in state"
                'eradicated',   # Covers: "Species eradicated"
                'questionable', # Covers: "Questionable presence
                                #          (cross-hatched)"
                ]
        PRESENCE_INDICATORS = [
            'present',   # From adjusted New England data, covers "present"
            'exotic',    # Covers: "Species present in state and exotic"
                         #     and "Species exotic and present"
            'waif',      # Covers: "Species waif"
            'noxious',   # Covers: "Species noxious"
            'and rare',  # Covers: "Species present and rare"
            'native',    # Covers: "Species present in state and native"
            'species present', # Covers: "Species present in state and
                               #          not rare"
            ]

        NON_NATIVE_PRESENCE_INDICATORS = [
            'present, non-native',   # From adjusted New England data
            'exotic',    # Covers: "Species present in state and exotic"
                         #     and "Species exotic and present"
            'waif',      # Covers: "Species waif"
            'noxious',   # Covers: "Species noxious"
            ]

        NATIVE_PRESENCE_INDICATORS = [
            'present, native',   # From adjusted New England data
            'and rare',  # Covers: "Species present and rare"
            'native',    # Covers: "Species present in state and native"
            'species present', # Covers: "Species present in state and
                               #          not rare"
            ]

        label = ''
        status = status.lower()

        # Look through the absence indicators first because otherwise
        # a "false-present" label could occur.
        for indicator in ABSENCE_INDICATORS:
            if indicator in status:
                label = 'absent'
                break
        # If an absence indicator did not set a label, look through the
        # presence indicators.
        if label == '':
            for indicator in NON_NATIVE_PRESENCE_INDICATORS:
                if indicator in status:
                    label = 'non-native'
                    break
            if label == '':
                for indicator in NATIVE_PRESENCE_INDICATORS:
                    if indicator in status:
                        label = 'native'
                        break

        return label

    def _add_name_to_title(self, scientific_name):
        """Add the plant name to the map's title."""
        title_text = self.get_title()
        sep_index = title_text.find(':')
        if sep_index > -1:
            title_text = title_text[sep_index + 1:].strip()
        title_text = '%s: %s' % (scientific_name, title_text)
        self.set_title(title_text)

    def _get_distribution_records(self, scientific_name):
        """Look up the plant and get its distribution records.
        """
        return models.Distribution.objects.filter(
                    scientific_name=scientific_name)

    def set_plant(self, scientific_name):
        """Set the plant to be shown and gather its data."""
        self.scientific_name = scientific_name
        records = self._get_distribution_records(self.scientific_name)
        if not records:
            # Distribution records might be listed under one of the
            # synonyms for this plant instead.
            try:
                taxon = models.Taxon.objects.get(
                    scientific_name=self.scientific_name)
                if taxon.synonyms:
                    for synonym in taxon.synonyms.all():
                        name = synonym.scientific_name
                        records = self._get_distribution_records(name)
                        if records:
                            break
            except ObjectDoesNotExist:
                pass  # Didn't find the plant in the database
        self.distribution_records = records

        # Only add the plant name to the title if distribution data are
        # found, to keep the title neutral in the event of junk in the URL.
        if records:
            self._add_name_to_title(self.scientific_name)

    def _order_labels(self, labels):
        """Put legend labels in display order."""
        all_labels = [item[0] for item in Legend.ITEMS]
        ordered_labels = [label for label in all_labels if label in labels]
        return ordered_labels

    def _shade_areas(self):
        """Set the colors of the counties (or, in the case of Canada,
        provinces, until county/district data become available) based
        on distribution data.
        """
        legend_labels_found = []
        if self.distribution_records:
            path_nodes = self.svg_map.xpath(self.PATH_NODES_XPATH,
                namespaces=NAMESPACES)

            # When shading a map area, iterate over the nodes rather
            # than selecting a node via XPath. Iterating is around twice
            # as fast as XPath, at least when breaking after finding a node
            # as is done for the county-level records.

            # Take a pass through the nodes and shade any
            # state-/province-/territory-level records.
            state_records = self.distribution_records.filter(county='')
            for record in state_records:
                state_id_piece = '%s_' % record.state.lower()
                for node in path_nodes:
                    node_id = node.get('id').lower()
                    if node_id.startswith(state_id_piece):
                        label = self._get_label_for_status(record.status)
                        if label not in legend_labels_found:
                            legend_labels_found.append(label)
                        box = Path(node)
                        box.color(Legend.COLORS[label])
                        # Keep going rather than break, because for each
                        # state-level record there will be multiple
                        # counties to shade.

            # Take a pass through the nodes and shade any county-level
            # records.
            county_records = self.distribution_records.exclude(county='')
            for record in county_records:
                state_and_county = '%s_%s' % (record.state.lower(),
                                              record.county.replace(
                                                  ' ', '_').lower())
                for node in path_nodes:
                    node_id = node.get('id').lower()
                    if node_id == state_and_county:
                        label = self._get_label_for_status(record.status)
                        if label not in legend_labels_found:
                            legend_labels_found.append(label)
                        box = Path(node)
                        box.color(Legend.COLORS[label])
                        break   # Move on to the next distribution record.

            legend_labels_found = self._order_labels(legend_labels_found)

        return legend_labels_found

    def shade(self):
        """Shade a New England plant distribution map. Assumes the method
        set_plant(scientific_name) has already been called.
        """
        legend_labels_found = self._shade_areas()
        self.legend.show_items(legend_labels_found)
        return self


class NewEnglandPlantDistributionMap(PlantDistributionMap):
    """Class for a map that shows New England county-level distribution
    data for a plant.
    """

    def __init__(self):
        # Note that this version of the New England counties map is
        # under the static directory. It is not to be confused with
        # versions in the "mapping" app's directory, which are used by
        # code that scans existing maps.
        blank_map_path  = GRAPHICS_ROOT + '/new-england-counties-scoured.svg'
        super(NewEnglandPlantDistributionMap, self).__init__(blank_map_path)


class UnitedStatesPlantDistributionMap(PlantDistributionMap):
    """Class for a map that shows United States county-level distribution
    data for a plant.
    """

    PATH_NODES_XPATH = 'svg:g/svg:path'

    def __init__(self):
        blank_map_path  = GRAPHICS_ROOT + '/us-counties-scoured.svg'
        super(UnitedStatesPlantDistributionMap, self).__init__(blank_map_path)


class NorthAmericanPlantDistributionMap(PlantDistributionMap):
    """Class for a map that shows North American distribution data for a
    plant. Data for the United States are shown at the county level. Data
    for Canada are currently shown at the province level, not the county
    or county equivalent level, because it is not yet available. Also,
    only the southern parts of eight Canadian provinces are shown so far,
    because that is the extent of the available data.
    """

    PATH_NODES_XPATH = 'svg:g/svg:path'

    def __init__(self):
        blank_map_path = GRAPHICS_ROOT + '/north-america-scoured.svg'
        super(NorthAmericanPlantDistributionMap, self).__init__(
            blank_map_path)

    def _get_distribution_records(self, scientific_name):
        """Look up the plant and get its distribution records.
        Exclude county-level records seen in the New England data.
        """
        return models.Distribution.objects.filter(
                    scientific_name=scientific_name
                ).exclude(
                    county__gt=''
                )

    def _shade_areas(self):
        """Set the colors of the states, provinces, or territories.
        Originally we expected county-level data, at least for the U.S.,
        so this routine shades all county paths within a state.
        """
        legend_labels_found = []
        if self.distribution_records:
            path_nodes = self.svg_map.xpath(self.PATH_NODES_XPATH,
                namespaces=NAMESPACES)
            for record in self.distribution_records.filter(county=''):
                for node in path_nodes:
                    id_province = node.get('id').split('_')[0].upper()
                    if id_province == record.state.upper():
                        label = self._get_label_for_status(record.status)
                        if label not in legend_labels_found:
                            legend_labels_found.append(label)
                        box = Path(node)
                        box.color(Legend.COLORS[label])
                        # Keep going rather than break, because
                        # there are often multiple paths to shade.

            legend_labels_found = self._order_labels(legend_labels_found)

        return legend_labels_found


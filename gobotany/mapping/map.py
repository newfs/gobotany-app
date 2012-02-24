from os.path import abspath, dirname
from django.core.exceptions import ObjectDoesNotExist
from lxml import etree
from gobotany.core import models

GRAPHICS_ROOT = abspath(dirname(__file__) + '/../static/graphics')
NAMESPACES = {'svg': 'http://www.w3.org/2000/svg'}

class Path(object):
    """Class for operating on a SVG path node."""
    STYLE_ATTR = 'style'

    def __init__(self, path_node):
        self.path_node = path_node

    def get_style(self):
        return self.path_node.get(Path.STYLE_ATTR)

    def set_style(self, value):
        self.path_node.set(Path.STYLE_ATTR, value)

    def color(self, fill_color, stroke_color=None):
        style = self.get_style()
        shaded_style = style.replace('fill:#fff', 'fill:%s' % fill_color)
        if stroke_color:
            shaded_style = shaded_style.replace('stroke:#000',
                'stroke:%s;' % str(stroke_color))
        self.set_style(shaded_style)

    def __str__(self):
        return '%s (%s)' % (self.path_node.get('id'), self.get_style())


class Legend(object):
    """Class for configuring the legend on a SVG plant distribution map."""

    # This list controls the order, label and color of legend items.
    ITEMS = [('native', '#78bf47'), ('rare', '#a7e37d'),
             ('introduced', '#fa9691'), ('invasive', '#f00'),
             ('historic', '#ccc'), ('absent', '#fff')]
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
        """Return the appropriate label for a distribution status string."""
        label = ''
        if 'exotic' in status:
           label = 'introduced'
        elif 'noxious' in status:
           label = 'invasive'
        elif 'extirpated' in status:
           label = 'historic'
        elif 'rare' in status:
           label = 'rare'
        elif 'native' in status or 'present' in status:
            label = 'native'
        elif 'absent' in status:
            label = 'absent'
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
        """Look up the plant and get its distribution records."""
        return (models.Distribution.objects.filter(
                scientific_name=scientific_name))

    def set_plant(self, scientific_name):
        """Set the plant to be shown and gather its data."""
        self.scientific_name = scientific_name
        records = self._get_distribution_records(self.scientific_name)
        if not records:
            # Distribution records might be listed under one of the
            # synonyms for this plant instead.
            try:
                taxon = models.Taxon.objects.get( \
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
            for record in self.distribution_records.all():
                state_and_county = '%s_%s' % (record.state.lower(),
                                              record.county.replace(
                                                  ' ', '_').lower())
                # Look through all the path nodes until the one for this
                # state and county is found. (Note: this is at least
                # twice as fast as selecting each node via XPath.)
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


    def _get_distribution_records(self, scientific_name):
        """Look up the plant and get its New England distribution records."""
        NEW_ENGLAND_STATES = ['CT', 'MA', 'ME', 'NH', 'RI', 'VT']
        return (models.Distribution.objects.filter(
                scientific_name=scientific_name,
                state__in=NEW_ENGLAND_STATES))


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


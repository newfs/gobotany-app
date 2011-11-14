import xml.etree.ElementTree as ET

from gobotany.core import models
from gobotany.settings import STATIC_ROOT

class Path(object):
    """Class for operating on a SVG path node."""
    STYLE_ATTR = 'style'
    FILL_OPACITY = 1
    STROKE_OPACITY = 1

    def __init__(self, path_node):
        self.path_node = path_node

    def get_style(self):
        return self.path_node.get(Path.STYLE_ATTR)

    def set_style(self, value):
        self.path_node.set(Path.STYLE_ATTR, value)

    def color(self, fill_color, stroke_color=None):
        style = self.get_style()
        shaded_style = style.replace('fill:#fff;',
                                     'fill:%s;' % fill_color)
        shaded_style = shaded_style.replace('fill-opacity:1;',
            'fill-opacity:%s;' % str(Path.FILL_OPACITY))
        shaded_style = shaded_style.replace('stroke-opacity:1;',
            'stroke-opacity:%s;' % str(Path.STROKE_OPACITY))
        if stroke_color:
            shaded_style = shaded_style.replace('stroke:#000000;',
                'stroke:%s;' % str(stroke_color))
        self.set_style(shaded_style)


class Legend(object):
    """Class for configuring the legend on a SVG plant distribution map."""

    # This list controls the order, label and color of legend items.
    ITEMS = [('native', '#78bf47'), ('rare', '#a7e37d'),
             ('introduced', '#fa9691'), ('invasive', '#f00'),
             ('historic', '#ccc'), ('absent', '#fff')]
    COLORS = dict(ITEMS)  # Colors for labels, ex.: COLORS['rare']

    def __init__(self, svg_map, maximum_items):
        self.box_nodes = svg_map.findall('{http://www.w3.org/2000/svg}rect')
        self.label_nodes = svg_map.findall('{http://www.w3.org/2000/svg}text')
        self.maximum_items = maximum_items

    def _set_item_label(self, label_node, label):
        label_text_node = label_node.find('{http://www.w3.org/2000/svg}tspan')
        label_text_node.text = label

    def _set_item(self, slot_number, fill_color, stroke_color, item_label):
        box_node_id = 'box%s' % str(slot_number)
        label_node_id = 'label%s' % str(slot_number)
        for box_node in self.box_nodes:
            if box_node.get('id') == box_node_id:
                box = Path(box_node)
                box.color(fill_color, stroke_color)
                break
        for label_node in self.label_nodes:
            if label_node.get('id') == label_node_id:
                self._set_item_label(label_node, item_label)
                break

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


class ChloroplethMap(object):
    """Base class for a chloropleth SVG map."""

    def __init__(self, blank_map_path, maximum_legend_items):
        self.svg_map = ET.parse(blank_map_path)
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
        return ET.tostring(self.svg_map.getroot())


class PlantDistributionMap(ChloroplethMap):
    """Base class for a map that shows plant distribution data."""

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
        title_text = '%s: %s' % (scientific_name, title_text)
        self.set_title(title_text)

    def _get_distribution_records(self, scientific_name):
        """Look up the plant and get its distribution records."""
        self.taxon = (models.Taxon.objects.filter(
                      scientific_name=scientific_name))
        if len(self.taxon) > 0:
            return (models.Distribution.objects.filter(
                    scientific_name=scientific_name))

    def set_plant(self, scientific_name):
        """Set the plant to be shown and gather its data."""
        self.scientific_name = scientific_name
        self._add_name_to_title(self.scientific_name)
        self.distribution_records = (self._get_distribution_records(
                                        self.scientific_name))

    def _shade_counties(self):
        """Set the colors of the counties based on distribution data."""
        inkscape_label = '{http://www.inkscape.org/namespaces/inkscape}label'
        path_nodes = self.svg_map.getiterator(
            '{http://www.w3.org/2000/svg}path')
        legend_labels_found = []
        for record in self.distribution_records.all():
            for node in path_nodes:
                if inkscape_label in node.keys():
                    label_val = node.attrib[inkscape_label] # ex.: Suffolk, MA
                    if not label_val.startswith('#'):  # Ignore #State_borders
                        county, state = label_val.split(', ')
                        if county == record.county and state == record.state:
                            label = self._get_label_for_status(record.status)
                            if label != '':
                                if label not in legend_labels_found:
                                    legend_labels_found.append(label)
                                box = Path(node)
                                box.color(Legend.COLORS[label])
                            break;   # Found matching county and state for
                                     # this record, so go to the next record.

        # Order the found labels as they are to be presented in the legend.
        all_labels = [item[0] for item in Legend.ITEMS]
        legend_labels_found = [label for label in all_labels
                               if label in legend_labels_found]
        return legend_labels_found

    def shade(self):
        """Shade a New England plant distribution map. Assumes the method
        set_plant(scientific_name) has already been called.
        """
        legend_labels_found = self._shade_counties()
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
        blank_map_path  = ''.join([STATIC_ROOT,
                                  '/graphics/new-england-counties.svg'])
        super(NewEnglandPlantDistributionMap, self).__init__(blank_map_path)


    def _get_distribution_records(self, scientific_name):
        """Look up the plant and get its New England distribution records."""
        NEW_ENGLAND_STATES = ['CT', 'MA', 'ME', 'NH', 'RI', 'VT']
        self.taxon = (models.Taxon.objects.filter(
                      scientific_name=scientific_name))
        if len(self.taxon) > 0:
            return (models.Distribution.objects.filter(
                    scientific_name=scientific_name,
                    state__in=NEW_ENGLAND_STATES))


class UnitedStatesPlantDistributionMap(PlantDistributionMap):
    """Class for a map that shows United States county-level distribution
    data for a plant.
    """

    def __init__(self):
        blank_map_path  = ''.join([STATIC_ROOT,
                                  '/graphics/us-counties.svg'])
        super(UnitedStatesPlantDistributionMap, self).__init__(blank_map_path)



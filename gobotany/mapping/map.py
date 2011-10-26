import xml.etree.ElementTree as ET

from gobotany.core import models
from gobotany.settings import STATIC_ROOT

class ChloroplethMap(object):
    """Base class for a chloropleth SVG map."""

    def __init__(self, blank_map_path, maximum_legend_items):
        self.svg_map = ET.parse(blank_map_path)
        self.maximum_legend_items = maximum_legend_items

    def tostring(self):
        return ET.tostring(self.svg_map.getroot())


class PlantDistributionMap(ChloroplethMap):
    """Base class for a map that shows plant distribution data."""

    def __init__(self, blank_map_path, maximum_legend_items):
        super(PlantDistributionMap, self).__init__(blank_map_path,
                                                   maximum_legend_items)
        self.scientific_name = None

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

    def set_plant(self, scientific_name):
        """Look up the plant and get its distribution records."""
        self.scientific_name = scientific_name
        self.taxon = (models.Taxon.objects.filter(
                      scientific_name=self.scientific_name))
        if len(self.taxon) > 0:
            self.distribution_records = (models.Distribution.objects.filter(
                scientific_name=self.scientific_name))



class NewEnglandPlantDistributionMap(PlantDistributionMap):
    """Class for a map that shows New England county-level distribution
    data for a plant.
    """

    def __init__(self):
        # Note that this version of the New England counties map is in
        # the static directory. It is not to be confused with versions
        # in the "mapping" app's directory, which are used by code that
        # scans existing maps.
        blank_map_path  = ''.join([STATIC_ROOT,
                                  '/graphics/new-england-counties.svg'])
        maximum_legend_items = 5
        super(NewEnglandPlantDistributionMap, self).__init__(blank_map_path,
            maximum_legend_items)

    def shade(self):
        """Shade a New England plant distribution map. Assumes the base
        class method set_plant(scientific_name) has already been called.
        """
        STROKE_OPACITY = 1
        FILL_OPACITY = 1

        # This list controls the order, label and color of legend items.
        LEGEND_ITEMS = [('native', '#78bf47'), ('rare', '#a7e37d'),
                        ('introduced', '#fa9691'), ('invasive', '#f00'),
                        ('historic', '#ccc'), ('absent', '#fff')]
        colors_for_labels = dict(LEGEND_ITEMS)

        # Prefix the map title with the plant name.
        title = self.svg_map.find('{http://www.w3.org/2000/svg}title')
        title.text = '%s: %s' % (self.scientific_name, title.text)

        # Set the colors of the counties based on distribution data.
        inkscape_label = '{http://www.inkscape.org/namespaces/inkscape}label'
        path_nodes = self.svg_map.findall('{http://www.w3.org/2000/svg}path')
        legend_labels_found = []
        for node in path_nodes:
            if inkscape_label in node.keys():
                label = node.attrib[inkscape_label]   # ex.: Suffolk, MA
                county, state = label.split(', ')
                county_record = (self.distribution_records.filter(
                    county=county, state=state))
                if len(county_record) > 0:
                    status = county_record[0].status
                    label = self._get_label_for_status(status)
                    if label not in legend_labels_found:
                        legend_labels_found.append(label)
                    if label != '':
                        hex_color = colors_for_labels[label]
                        style = node.get('style')
                        shaded_style = style.replace('fill:none;',
                            'fill:%s;' % str(hex_color))
                        shaded_style = shaded_style.replace(
                            'stroke-opacity:1;',
                            'stroke-opacity:%s;' % str(STROKE_OPACITY))
                        node.set('style', shaded_style)

        # Order the found labels as they are to be presented in the legend.
        all_labels = [item[0] for item in LEGEND_ITEMS]
        legend_labels_found = [label for label in all_labels
                               if label in legend_labels_found]

        # Set the colors and labels of the legend items.
        box_nodes = self.svg_map.findall('{http://www.w3.org/2000/svg}rect')
        label_nodes = self.svg_map.findall('{http://www.w3.org/2000/svg}text')

        for legend_slot_number in range(1, self.maximum_legend_items + 1):
            box_node_id = 'box%s' % str(legend_slot_number)
            label_node_id = 'label%s' % str(legend_slot_number)
            # Only show legend items for data values shown on this map.
            if len(legend_labels_found) >= legend_slot_number:
                # Show the legend item.
                item_label = legend_labels_found[legend_slot_number - 1]
                hex_color = colors_for_labels[item_label]
                box_stroke_color = '#000'
            else:
                # Do not show the legend item, and hide its box.
                item_label = ''
                hex_color = '#fff'
                box_stroke_color = '#fff'

            # Set the legend box color, or hide the box.
            for box_node in box_nodes:
                if box_node.get('id') == box_node_id:
                    style = box_node.get('style')
                    shaded_style = style.replace(
                        'fill:#000000;fill-opacity:0;',
                        'fill:%s;fill-opacity:%s;' % (hex_color,
                                                      str(FILL_OPACITY)))
                    shaded_style = shaded_style.replace('stroke:#000000;',
                        'stroke:%s;' % str(box_stroke_color))
                    box_node.set('style', shaded_style)
                    break
            # Set the legend label, or hide it.
            for label_node in label_nodes:
                if label_node.get('id') == label_node_id:
                    label_text_node = label_node.find( \
                        '{http://www.w3.org/2000/svg}tspan')
                    label_text_node.text = item_label
                    break

import xml.etree.ElementTree as ET

from gobotany.core import models
from gobotany.settings import STATIC_ROOT

class ChloroplethMap(object):
    """Base class for a chloropleth SVG map."""

    def __init__(self, blank_map_path):
        self.svg_map = ET.parse(blank_map_path)

    def tostring(self):
        return ET.tostring(self.svg_map.getroot())


class PlantDistributionMap(ChloroplethMap):
    """Base class for a map that shows plant distribution data."""

    def __init__(self, blank_map):
        super(PlantDistributionMap, self).__init__(blank_map)
        self.scientific_name = None

    def _get_label_for_status(self, status):
        """Return the appropriate label for a distribution status string."""
        label = ''
        if status.find('present') > -1:
            label = 'native'
            if status.find('rare') > -1:
                label = 'rare'
            elif status.find('exotic') > -1:
                label = 'introduced'
                if status.find('noxious') > -1:
                    label = 'invasive'
        elif status.find('extirpated') > -1:
            label = 'historic'
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
        super(NewEnglandPlantDistributionMap, self).__init__(blank_map_path)

    def shade(self):
        """Shade a New England plant distribution map. Assumes the base
        class method set_plant(scientific_name) has already been called.
        """
        STROKE_OPACITY = 1
        FILL_OPACITY = 1

        # This list controls the order, label and color of legend items.
        LEGEND_ITEMS = [('native', '#78bf47'), ('rare', '#a7e37d'),
                        ('introduced', '#fa9691'), ('invasive', '#f00'),
                        ('historic', '#ccc')]
        colors_for_labels = dict(LEGEND_ITEMS)

        # Prefix the map title with the plant name.
        title = self.svg_map.find('{http://www.w3.org/2000/svg}title')
        title.text = '%s: %s' % (self.scientific_name, title.text)

        # Set the colors of the counties based on distribution data.
        inkscape_label = '{http://www.inkscape.org/namespaces/inkscape}label'
        path_nodes = self.svg_map.findall('{http://www.w3.org/2000/svg}path')
        for node in path_nodes:
            if inkscape_label in node.keys():
                label = node.attrib[inkscape_label]   # ex.: Suffolk, MA
                county, state = label.split(', ')
                county_record = (self.distribution_records.filter(
                    county=county, state=state))
                if len(county_record) > 0:
                    status = county_record[0].status
                    label = self._get_label_for_status(status)
                    if label != '':
                        hex_color = colors_for_labels[label]
                        style = node.get('style')
                        shaded_style = style.replace('fill:none;',
                            'fill:%s;' % str(hex_color))
                        shaded_style = shaded_style.replace( \
                            'stroke-opacity:1;',
                            'stroke-opacity:%s;' % str(STROKE_OPACITY))
                        node.set('style', shaded_style)

        # Set the colors and labels of the legend items.
        box_nodes = self.svg_map.findall('{http://www.w3.org/2000/svg}rect')
        label_nodes = self.svg_map.findall('{http://www.w3.org/2000/svg}text')
        for (counter, item) in enumerate(LEGEND_ITEMS, start=1):
            item_label = item[0]
            hex_color = item[1]
            box_node_id = 'box%s' % str(counter)
            label_node_id = 'label%s' % str(counter)
            for box_node in box_nodes:
                if box_node.get('id') == box_node_id:
                    style = box_node.get('style')
                    shaded_style = style.replace(
                        'fill:#000000;fill-opacity:0;',
                        'fill:%s;fill-opacity:%s;' % (hex_color,
                                                      str(FILL_OPACITY)))
                    box_node.set('style', shaded_style)
                    break
            for label_node in label_nodes:
                if label_node.get('id') == label_node_id:
                    label_text_node = label_node.find( \
                        '{http://www.w3.org/2000/svg}tspan')
                    label_text_node.text = item_label
                    break

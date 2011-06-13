"""Scan a map to learn how a species is distributed."""

import xml.etree.ElementTree as etree
from collections import namedtuple

from PIL import Image

MapPoint = namedtuple('MapPoint', ['state', 'county', 'x', 'y'])

PIXEL_VALUES = [
    ((0, 128, 0), 'absent'),
    ((0, 255, 0), 'present'),
    ]

range3 = range(3)

def diagnose_pixel(pixel):
    for rgb, value in PIXEL_VALUES:
        dsq = sum((pixel[i] - rgb[i]) ** 2 for i in range3)
        if dsq < 100:
            return value
    raise ValueError('I cannot determine what the pixel {} means'.format(value))

class MapScanner(object):

    def __init__(self, svg_path):
        self.points = []

        root = etree.parse(svg_path)
        tspans = root.findall('.//{http://www.w3.org/2000/svg}tspan')
        for tspan in tspans:
            if not tspan.text:
                continue
            x = int(float(tspan.get('x')))  # int() forces pixel boundaries
            y = int(float(tspan.get('y')))
            s = tspan.text  # reach inside of the single <tspan> child
            state, county = s.split(None, 1)
            self.points.append(MapPoint(state=state, county=county, x=x, y=y))

        self.points.sort()

    def scan(self, map_image_path):
        im = Image.open(map_image_path)
        for point in self.points:
            value = diagnose_pixel(im.getpixel((point.x, point.y)))
            print point.state, point.county, value

if __name__ == '__main__':
    import os
    data = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
    ms = MapScanner(os.path.join(data, 'new-england-counties.svg'))
    ms.scan(os.path.join(data, 'Acorus americanus New England.png'))

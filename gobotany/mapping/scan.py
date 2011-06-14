"""Scan a map to learn how a species is distributed."""

import xml.etree.ElementTree as etree
from collections import namedtuple
from csv import DictReader

from PIL import Image

MapPoint = namedtuple('MapPoint', ['state', 'county', 'x', 'y'])
MapStatus = namedtuple('MapStatus', ['state', 'county', 'status'])

def c(rgbhex):
    """Convert 0x008000 to (0, 128, 0)."""
    rg, b = divmod(rgbhex, 0x100)
    r, g = divmod(rg, 0x100)
    return (r, g, b)

PIXEL_VALUES = [          # From the http://www.bonap.org/MapKey.html page:
    (c(0x008000), True),  # Species present in state and native
    (c(0x00FF00), True),  # Species present and not rare
    (c(0xFE0000), False), # Species extinct
    (c(0x00DD90), True),  # Species native, but adventive in state
    (c(0x3AB2E6), False), # Species waif    See http://en.wikipedia.org/wiki/Waif
    (c(0x0000EA), True),  # Species present in state and exotic
    (c(0xFFFF00), True),  # Species present and rare
    (c(0xFF00FE), True),  # Species noxious
    (c(0x000000), False), # Species eradicated
    (c(0xAD8E00), False), # Species not present in state
    (c(0xFE9900), False), # Species extirpated (historic)
    (c(0x00FFFF), True),  # Species exotic and present
    #(c(0x), True),  # Questionable Presence (cross-hatched)
    ]

del c
range3 = range(3)

def pixel_status(pixel):
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
        return [
            MapStatus(p.state, p.county, pixel_status(im.getpixel((p.x, p.y))))
            for p in self.points
            ]

if __name__ == '__main__':
    import os
    data = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
    ms = MapScanner(os.path.join(data, 'new-england-counties.svg'))
    if False:
        # Simple test; just print out data from one map.
        pngpath = os.path.join(data, 'Acorus americanus New England.png')
        for tup in ms.scan(pngpath):
            print tup
    if True:
        # Read in taxa.csv and compare.
        csvdir = os.path.join(data, '..', '..', 'gobotany-buildout', 'data')
        csvpath = os.path.join(csvdir, 'taxa.csv')
        with open(csvpath) as csvfile:
            for row in DictReader(csvfile):
                sn = row['Scientific_Name']

                pngpath = os.path.join(data, sn + ' New England.png')
                if not os.path.exists(pngpath):
                    continue
                tups = ms.scan(pngpath)
                nstates = set(s.state for s in ms.scan(pngpath))

                bstates = set(s.strip() for s in row['Distribution'].split('|'))

                for state in nstates - bstates:
                    print 'We think that {0} is in {1}'.format(sn, state)
                for state in bstates - nstates:
                    print 'BONAP thinks that {0} is in {1}'.format(sn, state)

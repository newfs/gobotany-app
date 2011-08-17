"""Scan a map to learn how a species is distributed."""

import csv
import os
import sys
import xml.etree.ElementTree as etree
from collections import namedtuple
from csv import DictReader
from os.path import dirname, join

from PIL import Image

Point = namedtuple('Point', ['x', 'y'])
MapPoint = namedtuple('MapPoint', ['state', 'county', 'x', 'y'])
MapStatus = namedtuple('MapStatus', ['state', 'county', 'status'])

# Turning pixel colors into species status.

def c(rgbhex):
    """Convert 0x008000 to (0, 128, 0)."""
    rg, b = divmod(rgbhex, 0x100)
    r, g = divmod(rg, 0x100)
    return (r, g, b)

PIXEL_STATUSES = [
    # From the http://www.bonap.org/MapKey.html page:
    (c(0x008000), 'present|native'),
    (c(0x00FF00), 'present'),
    (c(0xFE0000), 'absent|extinct'),
    (c(0x00DD90), 'present|adventive|native'),
    (c(0x3AB2E6), 'absent|waif'),
    (c(0x57A6FF), 'absent|waif'), # another waif color? see Galeopsis ladanum
    (c(0x0000EA), 'present|exotic'),
    (c(0xFFFF00), 'present|rare'),
    (c(0xFF00FE), 'present|noxious'),
    (c(0x000000), 'absent|eradicated'),
    (c(0xAD8E00), 'absent'),
    (c(0xFE9900), 'absent|extirpated'),
    (c(0x00FFFF), 'present|exotic'),
    ]

del c
range3 = range(3)

def pixel_status(pixel):
    for rgb, status in PIXEL_STATUSES:
        dsq = sum((pixel[i] - rgb[i]) ** 2 for i in range3)
        if dsq < 200:
            return status
    raise ValueError('I cannot determine what the pixel {0} means'
                     .format(pixel))

# The scanner class itself.

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

#

def scan(svg_path, mapdir, bonap_path):
    ms = MapScanner(svg_path)
    csv_writer = csv.writer(open(bonap_path, 'wb'))
    csv_writer.writerow(('scientific_name', 'state', 'county', 'status'))
    for pngname in os.listdir(mapdir):
        if not pngname.endswith('.png'):
            continue
        scientific_name = pngname[:-4]
        pngpath = join(mapdir, pngname)
        for tup in ms.scan(pngpath):
            row = [scientific_name, tup.state, tup.county, tup.status]
            csv_writer.writerow(row)

def report():
    pass

#

def main():
    thisdir = dirname(__file__)
    topdir = dirname(dirname(dirname(dirname(thisdir))))
    mapdir = join(topdir, 'kartesz_maps', 'New_England_maps')
    datadir = join(topdir, 'buildout-myplants', 'data')

    svg_path = join(join(thisdir, 'new-england-counties2.svg'))
    bonap_path = join(datadir, 'bonap.csv')
    taxa_path = join(datadir, 'taxa.csv')

    if sys.argv[1:] == ['scan']:
        scan(svg_path, mapdir, bonap_path)
    elif sys.argv[1:] == ['report']:
        report(bonap_path, taxa_path)
    else:
        print >>sys.stderr, 'usage: {0} scan|report'.format(sys.argv[0])

if __name__ == '__main__':
    main()

    if False:
        # Simple test; just print out data from one map.
        pngpath = join(data, 'Acorus americanus New England.png')
        for tup in ms.scan(pngpath):
            print tup
    if False:
        # Read in taxa.csv and compare.
        csvpath = join(csvdir, 'taxa.csv')
        with open(csvpath) as csvfile:
            total = misses = 0
            # go = False

            for row in DictReader(csvfile):
                total += 1
                sn = row['Scientific__Name']
                print 'SN:', sn, '/ Distribution:', repr(row['Distribution'])

                # Skip immediately to a later species in the file.
                # if sn == 'Galeopsis ladanum':
                #     go = True
                # if not go:
                #     continue

                pngpath = join(mapdir, sn + '.png')
                if not os.path.exists(pngpath):
                    print 'No map for species {0}'.format(sn)
                    misses += 1
                    continue
                tups = ms.scan(pngpath)
                for tup in tups:
                    print '  ', sn, tup.status, tup.state, tup.county
                bstates = set(s.state for s in tups if s.status)

                distribution = row['Distribution'].strip()
                if not distribution:
                    print 'We have no distribution for {0}'.format(sn)
                    continue
                nstates = set(s.strip() for s in distribution.split('|'))

                if nstates == bstates:
                    print 'Everything matches perfectly for {0}'.format(sn)
                    continue
                ours = nstates - bstates
                theirs = bstates - nstates
                if ours or theirs:
                    print sn,
                if ours:
                    print 'NEWFS says', ' '.join(ours),
                if theirs:
                    print 'BONAP says', ' '.join(theirs),
                print

        print '%d/%d (%f%%) species have images' % (
            total - misses, total, 100. * (total - misses) / total)

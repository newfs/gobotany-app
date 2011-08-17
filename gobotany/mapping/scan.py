"""Scan a map to learn how a species is distributed."""

import csv
import os
import sys
import xml.etree.ElementTree as etree
from collections import defaultdict, namedtuple
from csv import DictReader
from operator import itemgetter
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
        #print map_image_path
        im = Image.open(map_image_path)
        statuses = []
        for p in self.points:
            #print p.state, p.county, p.x, p.y, im.getpixel((p.x, p.y))
            status = pixel_status(im.getpixel((p.x, p.y)))
            statuses.append(MapStatus(p.state, p.county, status))
        return statuses

#

def scan(svg_path, mapdir, bonap_path):
    ms = MapScanner(svg_path)
    csv_writer = csv.writer(open(bonap_path, 'wb'))
    csv_writer.writerow(('scientific_name', 'state', 'county', 'status'))
    for pngname in sorted(os.listdir(mapdir)):
        if not pngname.endswith('.png'):
            continue
        # if pngname < 'Sanicula canadensis':
        #     # Skip ahead to a problematic map, for faster debugging
        #     continue
        scientific_name = pngname[:-4]
        pngpath = join(mapdir, pngname)
        for tup in ms.scan(pngpath):
            row = [scientific_name, tup.state, tup.county, tup.status]
            csv_writer.writerow(row)

def report(bonap_path, taxa_path):

    # Make a dictionary of BONAP presence: scientific_name -> {state, ...}

    bonap_reader = csv.DictReader(open(bonap_path, 'rb'))
    bonap_states = defaultdict(set)
    for row in bonap_reader:
        if None in row.values():
            # Survive a partially-written row, in case reports are being
            # run while bonap.csv itself is being regenerated.
            break
        state_set = bonap_states[row['scientific_name']]
        if 'present' in row['status']:
            state_set.add(row['state'])

    # Compare BONAP's ideas to our own.

    taxa_reader = DictReader(open(taxa_path, 'rb'))
    total = misses = 0
    rows = sorted(taxa_reader, key=itemgetter('Scientific__Name'))

    for row in rows:
        total += 1
        sn = row['Scientific__Name']
        #print 'SN:', sn, '/ Distribution:', repr(row['Distribution'])

        if sn not in bonap_states:
            # Accept a map named "Asplenium trichomanes ssp. trichomanes"
            # for the species we call simply "Asplenium trichomanes"
            sn = '{0} ssp. {1}'.format(sn, sn.split()[1])

        bstates = bonap_states.get(sn)
        if bstates is None:
            print '{0} - BONAP has no map'.format(sn),
            similars = [ n for n in bonap_states if n.startswith(sn+' ') ]
            if similars:
                print '(but does have {0})'.format(
                    ', '.join('"{0}"'.format(s) for s in similars)),
            print
            misses += 1
            continue

        distribution = row['Distribution'].strip()
        if not distribution:
            print '{0} - our taxa.csv has no distribution'.format(sn)
            continue

        nstates = set(s.strip() for s in distribution.split('|'))

        if nstates == bstates:
            print '{0} - perfect match'.format(sn)
            continue
        ours = nstates - bstates
        theirs = bstates - nstates
        if ours or theirs:
            print sn,
            print '- both={0}'.format('|'.join(nstates & bstates)),
        if ours:
            print 'newfs_only={0}'.format('|'.join(ours)),
        if theirs:
            print 'bonap_only={0}'.format('|'.join(theirs)),
        print

    print '%d/%d (%f%%) species have images' % (
        total - misses, total, 100. * (total - misses) / total)

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

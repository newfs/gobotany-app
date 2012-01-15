"""Scan a map to learn how a species is distributed."""

import argparse
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

THRESHOLD = 999

def pixel_status(pixel):
    answer = None
    for rgb, status in PIXEL_STATUSES:
        dsq = sum((pixel[i] - rgb[i]) ** 2 for i in range3)
        if dsq < THRESHOLD:
            answer = status if (answer is None) else ValueError
    if answer is not None and answer is not ValueError:
        return answer
    e = ValueError(
        'I cannot determine what pixel {0} = {1:02x}{2:02x}{3:02x} means'
        .format(pixel, pixel[0], pixel[1], pixel[2])
        )
    e.report = 'Here is how it measures up to the colors we know about:\n'
    for rgb, status in PIXEL_STATUSES:
        dsq = sum((pixel[i] - rgb[i]) ** 2 for i in range3)
        e.report += ' {0} {1} {2}\n'.format(rgb, status, dsq)
    raise e

# How to determine how much an image has been scaled.

def brightness_of(color):
    # We refuse to let the brightness fall to zero, since that would
    # make the `center` forumla attempt a divide-by-zero.
    return float(color[0] + color[1] + color[2])

Y = namedtuple('Y', 'value y')

def find_map_scale(im):
    y_straddle = range(2180, 2300)  # straddles border of New York state
    samples = [ Y(brightness_of(im.getpixel((0, y))), y) for y in y_straddle ]
    samples.sort()

    # Ignore any zero pixels in the middle of the black line.

    n = 0
    while samples[n].value == 0:
        n += 1

    # Interpolate between the two dim pixels astride the line's center.

    a, b = samples[n], samples[n+1]
    center = a.y + (b.y - a.y) * a.value / (a.value + b.value)

    # Deduce how much the image has been scaled relative to the
    # canonical image that we used to map county pixels.

    expected_center = 2226.625
    return center / expected_center

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
        scale = find_map_scale(im)
        statuses = []
        for p in self.points:
            #print p.state, p.county, p.x, p.y, im.getpixel((p.x, p.y))
            x, y = p.x * scale, p.y * scale
            try:
                status = pixel_status(im.getpixel((x, y)))
            except Exception as e:
                e.path = map_image_path
                e.scale = scale
                e.county = p.county
                e.xy = p.x, p.y
                e.xy2 = x, y
                raise
            statuses.append(MapStatus(p.state, p.county, status))
        return statuses

#

def scan(svg_path, mapdir, bonap_path):
    ms = MapScanner(svg_path)
    csv_writer = csv.writer(open(bonap_path, 'wb'))
    csv_writer.writerow(('scientific_name', 'state', 'county', 'status'))
    log_write = open(bonap_path.replace('csv', 'log'), 'w').write
    for pngname in sorted(os.listdir(mapdir)):
        if not pngname.endswith('.png'):
            continue
        # if pngname < 'Sanicula canadensis':
        #     # Skip ahead to a problematic map, for faster debugging
        #     continue
        scientific_name = pngname[:-4]
        pngpath = join(mapdir, pngname)
        try:
            tuples = ms.scan(pngpath)
        except ValueError as e:
            log_write(
                'Error\n'
                'Path: {0}\n'
                'Scale: {1}\n'
                'County: {2} at {3}\n'
                '{4}\n{5}'
                '\n'
                .format(e.path, e.scale, e.county, e.xy2, str(e), e.report)
                )
            continue
        for tup in tuples:
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
    parser = argparse.ArgumentParser(description='Process some integers.')
    subparsers = parser.add_subparsers(
        dest='command', help='designate an action to run')

    parser_s = subparsers.add_parser(
        'scan', help='Scan New England BONAP maps for distribution data')
    parser_s.add_argument('mapdir', help='The directory of BONAP maps')

    parser_r = subparsers.add_parser(
        'report', help='Compare BONAP distribution data with NEWFS data')
    parser_r  # (add future arguments here)

    args = parser.parse_args()

    thisdir = dirname(__file__)
    topdir = dirname(dirname(dirname(dirname(thisdir))))
    datadir = join(topdir, 'buildout-myplants', 'data')

    svg_path = join(join(thisdir, 'new-england-counties2.svg'))
    bonap_path = join(datadir, 'bonap.csv')
    taxa_path = join(datadir, 'taxa.csv')

    if args.command == 'scan':
        scan(svg_path, args.mapdir, bonap_path)
    elif args.command == 'report':
        report(bonap_path, taxa_path)
    else:
        print >>sys.stderr, 'usage: {0} scan|report'.format(sys.argv[0])

if __name__ == '__main__':
    main()

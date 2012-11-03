"""Command-line utility to import figure images from zip file."""

import Image
import argparse
import os
import re
import zipfile
from StringIO import StringIO

def figure_number(name):
    if '/maps/' in name:
        return None
    if '/prog-keep/' in name:
        return None
    numbers = re.findall('\d+(?=[^/]*$)', name)
    if not numbers:
        return None
    return int(numbers[-1])

def main():
    parser = argparse.ArgumentParser(
        description='import dkey figures from zip file')
    parser.add_argument('path', help='path to "flora-illustrations" zip file')
    args = parser.parse_args()

    z = zipfile.ZipFile(args.path)
    names = set(name for name in z.namelist()
                if figure_number(name) is not None)

    if not os.path.isdir('dkey-figures'):
        os.mkdir('dkey-figures')

    for name in names:
        z.open(name)
        sio = StringIO(z.open(name).read())
        image = Image.open(sio)
        number = figure_number(name)
        path = 'dkey-figures/figure-{}.png'.format(number)
        image.save(path)


if __name__ == '__main__':
    main()

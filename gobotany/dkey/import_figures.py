"""Command-line utility to import figure images from zip file."""

import argparse
import zipfile

def main():
    parser = argparse.ArgumentParser(
        description='import dkey figures from zip file')
    parser.add_argument('path', help='path to "flora-illustrations" zip file')
    args = parser.parse_args()

    z = zipfile.ZipFile(args.path)

if __name__ == '__main__':
    main()

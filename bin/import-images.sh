#!/bin/bash

set -e -v
cd $(dirname "$0")/..

# Our blazing-fast taxon image import routine, that fetches a single
# ls-R resource from S3 and then uses "bulkup" to create corresponding
# rows in the content-image table.

python -m gobotany.core.importer taxon-images

# Now that the taxon images are loaded, we can rebuild various "sample"
# image collections that are subsets of our taxon image set.

python -m gobotany.core.rebuild sample_pile_group_images
python -m gobotany.core.rebuild sample_pile_images

# Slow image-import routines, that actually ask S3 to list the contents
# of several folders (a slow operation to begin with), and that then use
# the Django ORM to actually create database rows.

# python -m gobotany.core.importer character-images data/characters.csv
# python -m gobotany.core.importer character-value-images data/character_values.csv
# python -m gobotany.core.importer glossary-images data/glossary.csv
python -m gobotany.core.importer home-page-images

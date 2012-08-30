#!/bin/bash

set -e

# Make a recursive list of all images in the taxon-images S3 directory
# and save the list to a compressed text file also stored in S3.

source $(dirname "$0")/s3-init.sh
TEMP=$(mktemp)
s3cmd ls -r s3://newfs/taxon-images/ | gzip -c9 > $TEMP
s3cmd put $TEMP s3://newfs/ls-taxon-images.gz
rm $TEMP

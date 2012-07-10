#!/bin/bash

set -e

# Our blazing-fast taxon image import routine, that fetches a single
# ls-R resource from S3 and then uses "bulkup" to create corresponding
# rows in the content-image table.

source $(dirname "$0")/s3-init.sh
python -m gobotany.core.importer taxon-images

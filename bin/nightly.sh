#!/bin/bash

set -e

if [ -z "$READ_ONLY" ]
then
    $(dirname "$0")/s3imagescan.sh
    $(dirname "$0")/s3thumbnail.sh
else
    echo
    echo '$READ_ONLY is set - skipping S3 scanning and thumbnailing'
    echo
fi
$(dirname "$0")/load images

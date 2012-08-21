#!/bin/bash

set -e

$(dirname "$0")/s3imagescan.sh
$(dirname "$0")/s3thumbnail.sh
$(dirname "$0")/s3imageload.sh

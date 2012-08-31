#!/bin/bash

set -e -v
cd $(dirname "$0")/..

bin/s3-init.sh
s3cmd get --skip-existing s3://newfs/data-dkey/110330_fone_test_05.xml
python -m gobotany.dkey.xml_import

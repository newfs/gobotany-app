#!/bin/bash

set -e
cd $(dirname "$0")/..

python -m gobotany.core.rebuild sample_pile_group_images \
    data/pile_group_info.csv
python -m gobotany.core.rebuild sample_pile_images \
    data/pile_info.csv

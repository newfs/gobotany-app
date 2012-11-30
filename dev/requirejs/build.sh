#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")
REQUIREJS="$PWD"
DEV=$REQUIREJS/..
cd $DEV

BUILD_PROFILE=$REQUIREJS/heroku.build.js

# Start the build

source $DEV/utils/install-node
$DEV/node/bin/r.js -o $BUILD_PROFILE "$@"

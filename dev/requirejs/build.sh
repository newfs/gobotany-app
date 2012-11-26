#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")
REQUIREJS="$PWD"
DEV=$REQUIREJS/..

BUILD_PROFILE=$REQUIREJS/heroku.build.js

# Start the build

source $DEV/install-node
$DEV/node/bin/r.js -o $BUILD_PROFILE "$@"

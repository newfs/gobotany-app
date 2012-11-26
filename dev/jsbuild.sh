#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")
DEV="$PWD"

if [ "$(uname -s)" == "Darwin" ]
then
    # Because readlink on Mac OS X lacks -f, use the compatible greadlink
    # instead. To get greadlink, install the MacPorts package coreutils.
    APP=$(greadlink -f $DEV/..)
else
    APP=$(readlink -f $DEV/..)
fi

# Nasty hack for dealing with Ember.js.  Ember.js is written using EcmaScript3
# reserved words for some of it's identifiers, and our build system currently defaults
# to EcmaScript3 compatibility, causing compiler errors.  As a (hopefully) temporary
# solution, we'll edit out the bad identifiers right before each build.
# NOTE: Each of these is very specific, because there are places in the Ember code
# dealing with it's compiler for Handlebars templates, and we don't want to mess with that.
EMBER_FILE=$APP/gobotany/static/scripts/lib/ember-1.0.pre.js
EMBER_HACK='sed -e "s/(char/(chr/g" -e "s/char)/chr)/g" -e "s/\.volatile/.safe_volatile/g"'

if ! grep -q safe_volatile $EMBER_FILE
then
    echo "*** Applying Ember Hack ***"
    cp -p $EMBER_FILE $EMBER_FILE.orig

    if [ "$(uname -s)" == "Darwin" ]
    then
        # Because sed on Mac OS X requires an extension when editing
        # in-place, supply a zero-length extension (which means no backup
        # will be saved).
        sed -i '' -e "s/(char/(chr/g" -e "s/char)/chr)/g" -e "s/\.volatile/.safe_volatile/g" $EMBER_FILE
    else
        eval $EMBER_HACK -i $EMBER_FILE
    fi
fi

$DEV/requirejs/build.sh

if [ -f $EMBER_FILE.orig ]
then
    echo "*** Undoing Ember Hack ***"
    mv $EMBER_FILE.orig $EMBER_FILE
fi

echo "Copying compiled javascript file to $APP/gobotany/static/js"
mkdir -p $APP/gobotany/static/js
cp $DEV/requirejs/build/gobotany.application.js \
   $APP/gobotany/static/js/gobotany.application.js

echo "Build Complete!"
echo "See jsbuild.log for details"

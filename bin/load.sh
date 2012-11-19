#!/bin/bash

# Build the base Go Botany database.

admin () {
    django-admin.py "$@" --settings gobotany.settings
}

HERE=$(dirname "$0")

set -e
admin syncdb --noinput
admin migrate
python -m gobotany.core.importer zipimport
$HERE/import-images.sh
$HERE/import-dkey.sh
admin rebuild_index --noinput
$HERE/test.sh

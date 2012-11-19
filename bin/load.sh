#!/bin/bash

# Build the base Go Botany database.

admin () {
    django-admin.py "$@" --settings gobotany.settings
}

set -e
admin syncdb --noinput
admin migrate
python -m gobotany.core.importer zipimport
$(dirname "$0")/import-images.sh
$(dirname "$0")/import-dkey.sh
admin rebuild_index --noinput

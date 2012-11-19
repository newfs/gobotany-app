#!/bin/bash

# Run our tests.

admin () {
    django-admin.py "$@" --settings gobotany.settings
}

# This list of modules is also maintained in tox.ini

admin test \
    api core dkey mapping \
    plantoftheday plantshare \
    search simplekey site taxa

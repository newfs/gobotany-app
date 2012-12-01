Go Botany
=========

Running Go Botany on your workstation
-------------------------------------

First, check out the repository and run `dev/setup` to install the
application and its dependencies in a Python virtual environment (that
lives inside of `dev/venv` in case you ever need to access it):

    git clone git@github.com:newfs/gobotany-app.git
    cd gobotany-app
    dev/setup

Next, make sure that you can access your local PostgreSQL server, which
you can confirm with a quick `psql -l`, and then start up a Solr full
text index server with:

    dev/start-solr

Finally, activate the virtual environment so that Python run from your
shell has access to the Go Botany application and its dependencies:

    source dev/activate

At this point the application should at least run, even though most
pages will give errors if your database is not set up yet.  To start the
application, simply run:

    dev/django runserver

You should then be able to visit the application at:

    http://localhost:8000/

If you are starting fresh and have no database set up yet, or want to
start over because some tables have changed or Sid had released a new
CSV file, then you can rebuild the database with these commands (the
first one will give an error if you do not have a `gobotany` database
already sitting in your way; in that case, ignore the error):

    dropdb gobotany
    createdb -E UTF8 gobotany
    bin/load

At this point you are done installing and should be able to test and
develop the application!

If you want to rebuild our minified JavaScript in preparation for a
deploy to production, run:

    dev/jsbuild

Our various tests can be run with three commands:

    dev/test-browser
    dev/test-js
    dev/test-python


Additional notes on workstation use
-----------------------------------

TODO: update this section

Here are some things you may run into when working with the above on
your workstation.

Before working, ensure you have your AWS credentials set in your
environment variables, which is usually accomplished by sourcing a shell
script kept outside the repository. This is needed to ensure tests will
pass and image importing will work.

When running dev/tox for the first time, especially if the database does not
exist yet, many test failures will occur. This is expected. The tests
should eventually all pass after the bin/load step is run.

If you want to do a fresh import of all data, first run:

    dropdb gobotany
    createdb -E UTF8 gobotany

If you are working on the Importer (gobotany/core/importer.py), be sure
to run dev/tox again each time before trying to run bin/load, the script
that executes the importer code. Running dev/tox is necessary to actually
package up and execute the version of importer.py that includes your local
changes.

You may need to have the virtual environment activated (source
dev/activate) before you are able to successfully run bin/load.
Otherwise, bin/load may give an error that it could not import the
gobotany.settings module to run syncdb. It is unclear yet whether this
is always so or only happens under certain conditions. 


Installing Go Botany on Heroku
------------------------------

Start by checking out this "gobotany-app" repository on your machine:

    git clone git@github.com:newfs/gobotany-app.git
    cd gobotany-app

Follow steps 1–3 at `http://devcenter.heroku.com/articles/quickstart`_
so that you can run the ``heroku`` command, then use the following
command to create and provision a new app on Heroku:

    heroku create
    heroku addons:add heroku-postgresql:basic
    heroku addons:add memcache:5mb
    heroku addons:add websolr:cobalt
    heroku pg:wait
    git push heroku master

Once the Postgres database is up and running, note its color (like "RED"
or "SILVER"), and promote it to being the "main database" for the app:

    heroku pg:promote <color>

Add three configuration variables to your Heroku app, so that Go Botany
will be able to scan its S3 image repository:

    heroku config:add AWS_ACCESS_KEY_ID=...
    heroku config:add AWS_SECRET_ACCESS_KEY=...
    heroku config:add AWS_STORAGE_BUCKET_NAME=newfs

The application will now be up and running.  You can find its URL with
the ``heroku apps:info`` command.  When you visit, you will see an
exception, because the database tables that it needs have not yet been
created.  To set up the database, run these commands:

    heroku config:add DJANGO_SETTINGS_MODULE=gobotany.settings
    heroku run django-admin.py syncdb --noinput
    heroku run python -m gobotany.core.importer zipimport
    heroku run bin/import-images.sh
    heroku run bin/import-dkey.sh

Prepare Solr by first generating your Solr schema:

    heroku run django-admin.py build_solr_schema > schema.xml

Once this file exists, you can visit the Heroku web site, navigate to
your app's configuration, select the addon "Websolr", choose the section
"Advanced Configuration", and paste in the contents of ``schema.xml``
that you just created.  Once the schema is installed (give it a few
minutes to make sure the change has the chance to propagate to WebSolr's
servers), you can build the Solr index and thereby activate the Go
Botany site's search field:

    heroku run django-admin.py rebuild_index --noinput


Running the automated tests
---------------------------

TODO: update this section

To run all the tests:

    gobotany-deploy $ ./test-all.sh

#### Python ####

These are a mix of unit tests and functional tests. To run the tests for
all of our Django apps:

    gobotany-deploy $ ./test-python.sh

To run the tests for a subset of the Django apps, add the app names:

    gobotany-deploy $ ./test-python.sh api core

#### JavaScript ####

    gobotany-deploy $ ./test-js.sh

If you want to run a subset of the tests, add the test class name:

    gobotany-deploy $ ./test-js.sh test/Filter.js

#### Selenium ####
   
These tests are intended to cover things that cannot be tested without a
browser and JavaScript. To run them:

    gobotany-deploy $ ./test-browser.sh

You can pass a parameter in the accustomed way to run all tests in a test
class, or a single test:

    gobotany-deploy $ ./test-browser.sh FilterFunctionalTests

    gobotany-deploy $ ./test-browser.sh FilterFunctionalTests.test_multiple_choice_filters

Detailed notes are in:
    
    gobotany-app/gobotany/simplekey/testdir/README-SELENIUM.txt


Testing and adjusting the search feature
----------------------------------------

The Go Botany search feature uses Haystack and Solr.

Our unit and functional tests aim to ensure various aspects of the search
feature including desired ranking.

Ranking relies mostly on Haystack document boost, as seen in several
places in our `search_indexes.py`. For more fine-grained control where
boost is not enough, some hidden repeated keywords are added to search
indexes such as in the `search_text_species.txt` template.

To adjust ranking: cycle through running the functional tests, adjusting
the boosts in `search_indexes.py`, and, if necessary, adjusting the
hidden-keyword sections at the end of `search_*.txt` templates. The Solr
Admin full interface, which allows examining details including ranking
scores, may also be helpful:

    http://localhost:8983/solr/admin/form.jsp

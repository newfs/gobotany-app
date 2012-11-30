Go Botany
=========

Running Go Botany on your workstation
-------------------------------------

Start by checking out this “gobotany-app” repository on your machine,
then running the “tox” Python testing tool:

    git clone git@github.com:newfs/gobotany-app.git
    cd gobotany-app
    tox

This will create a virtual environment (peek inside of `.tox` to see it)
where the Go Botany dependencies are all installed. You can then get the
application running with three commands:

    dev/start-solr
    bin/load
    dev/django runserver

At this point you are done installing and should be able to test and
develop the application!

Should you ever want a Python prompt that has access to Go Botany's
dependencies, you can run:

    source dev/activate

If you want to rebuild our minified JavaScript in preparation for a
deploy to production, run:

    dev/jsbuild

Our various tests can be run with three commands:

    tox
    dev/test-browser
    dev/test-js

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

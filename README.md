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
    dev/load

At this point you are done installing and should be able to test and
develop the application!

If you ever need to activate the virtual environment so that Python
prompts or scripts run from your shell have access to the Go Botany
application and its dependencies, then enter:

    source dev/activate

If you want to rebuild our minified JavaScript in preparation for a
deploy to production, run:

    dev/jsbuild

Our various tests can be run with three commands:

    dev/test-browser
    dev/test-js
    dev/test-python


Additional notes on workstation use
-----------------------------------

Here are some things you may run into when working with the above on
your workstation.

Before working, ensure you have your AWS credentials set in your
environment variables, which is often accomplished by sourcing a shell
script that the developer keeps outside the repository.  This is needed
to ensure that PlantShare image importing will work.


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

To run our Python tests you can either:

    dev/test-python             # to run all tests
    dev/test-python api site    # to hand-pick Django apps to test

To run our JavaScript tests, run:

    dev/test-js                 # to run all tests
    dev/test-js test/Filter.js  # to select which modules to test

Our selenium-powered browser tests are intended to cover things that
cannot be tested without a browser and JavaScript.  To run them:

    dev/test-browser                           # to run all tests
    dev/test-browser.sh FilterFunctionalTests  # select which tests

Detailed notes about testing under selenium can be found in:

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

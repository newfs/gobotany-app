
Running Functional Tests With Selenium
======================================

Our buildout now installs the most recent Selenium Python library, which
powers the functional tests in the accompanying `test_fbasic.py` file.
It also installs `unittest2` so that we can design these tests using all
of the latest idioms, even though some of these were not yet available
when Python 2.6 was released.

Against a local browser
-----------------------

The easiest way to run these functional tests is like this::

  $ bin/unit2 gobotany.simplekey.test.test_fbasic

The new Selenium 2 technology does not require a server; the Python code
will start up a web browser directly.

Against a remote browser
------------------------

If you want to run a standalone Selenium server the old-fashioned way -
maybe to allow IE on a Windows machine to be driven by the test suite
running on Linux or Mac OS - then on the machine with the browser you
want to test you can run::

  $ java -jar selenium-server-standalone-2.0b3.jar -browserSessionReuse

The standalone server will print out a URL that you can then supply to
your tests through an environment variable::

  $ SELENIUM=http://127.0.0.1:4444/wd/hub \
      bin/unit2 gobotany.simplekey.test.test_fbasic

Hitting sites other than localhost
----------------------------------

Either of the above commands can be supplemented with a `SIMPLEHOST`
environmental variable to make them look for the web application to be
running somewhere other than `localhost:8000` which is where the tests
expect it by default.  Just prepend either of the above command lines
with something like::

  $ SIMPLEHOST=192.168.1.5:8000 ...

Or, you could even point the test suite directly at the version of the
Simple Key that we have running on our EC2 instance::

  $ SIMPLEHOST=simplekey.newfs.org ...

Running your tests using Sauce Labs
-----------------------------------

Finally, if you want to use Sauce Labs to run your suite, then you can
provide the remote URL in your `SELENIUM` environment variable.  So you
could run Sauce Labs against our EC2 instance by running something like
this::

  $ SELENIUM=http://your_username:7ae65a2a-925f-db4d-925f-4d2b7e5e1b33@ondemand.saucelabs.com:80/wd/hub \
      SIMPLEHOST=simplekey.newfs.org \
      bin/unit2 gobotany.simplekey.test.test_fbasic

If you want Sauce to hit the server running on your localhost (but be
warned that this can be very slow unless you are on a network with a
fast uplink back to the Internet, which will cost testing time for your
Sauce Labs account!), then use the `sauce_connect` application to tell
your Sauce hosts to redirect that hostname back to your local machine
over an SSH tunnel::

  ./sauce_connect -u USERNAME -k KEY -s localhost -p 8000 \
    -d simplekey.org -t 80

Then just tell the tests to hit that fake domain name you just
established over at Sauce Labs::

  $ SELENIUM=... SIMPLEHOST=simplekey.org \
      bin/unit2 gobotany.simplekey.test.test_fbasic

Good luck, and ask Brandon about any questions you have!

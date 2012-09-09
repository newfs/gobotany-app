"""Library of helpers for our tests."""

from django.conf import settings
from django.db import transaction
from django.test.testcases import (
    DEFAULT_DB_ALIAS, TestCase, connections,
    disable_transaction_methods, restore_transaction_methods,
    )
from django.test.client import Client
from lxml import etree
from lxml.cssselect import CSSSelector
from psycopg2 import OperationalError
from warnings import warn


anchor_selector = CSSSelector('a')

class FunctionalCase(TestCase):
    """Support functional tests against a fully-populated database.

    Tests under the control of this class do not run against the empty
    test database that Django sets up and that, per our settings.py,
    runs inside of a sqlite3 in-memory database.  Instead, they run
    against the real database on the developer's machine (or the real
    database in production, if that is where someone invokes these
    tests!) but inside of transactions so that everything is rolled back
    to normal after each test runs.

    """
    @classmethod
    def setUpClass(cls):
        """Functional tests need a fully-imported database.

        While this class is in use, we hide the 'default' test database
        configuration, that points at a sqlite3 in-memory database, set
        aside so that we can talk to our real Go Botany database (or
        whatever copy of it is running on a developer's box) to see how
        pages render against our real data.

        """
        cls._default_config = connections.databases['default']
        connections.databases['default'] = settings.REAL_DATABASE

        cls._default_connection = connections._connections.default
        del connections._connections.default

        try:
            connections['default'].cursor()
        except OperationalError:
            warn('Cannot find default database, skipping functional tests')
            cls.__unittest_skip__ = True
            cls.tearDownClass()
        else:
            cls.__unittest_skip__ = False

    @classmethod
    def tearDownClass(cls):
        """Restore everything."""

        connections.databases['default'] = cls._default_config
        connections._connections.default = cls._default_connection

    def _fixture_setup(self):
        """Run inside a transaction, but without wiping the database."""

        if getattr(self, 'multi_db', False):
            databases = connections
        else:
            databases = [DEFAULT_DB_ALIAS]

        for db in databases:
            transaction.enter_transaction_management(using=db)
            transaction.managed(True, using=db)
        disable_transaction_methods()

    def _fixture_teardown(self):
        """Copied from the django.test.testcases versions of this method."""

        if getattr(self, 'multi_db', False):
            databases = connections
        else:
            databases = [DEFAULT_DB_ALIAS]

        restore_transaction_methods()
        for db in databases:
            transaction.rollback(using=db)
            transaction.leave_transaction_management(using=db)

    # Helpers to make writing tests more fun.  Note that these are
    # designed for basic symmetry with out Selenium-powered tests, so
    # that our two flavors of functional test do not look entirely
    # different!

    def get(self, url):
        self.response = Client().get(url)
        parser = etree.HTMLParser()
        self.tree = etree.fromstring(self.response.content, parser)

    def css(self, selector):
        return CSSSelector(selector)(self.tree)

    def css1(self, selector):
        return CSSSelector(selector)(self.tree)[0]

    def link_saying(self, text):
        links = anchor_selector(self.tree)
        for link in links:
            if link.text == text:
                return link
        raise ValueError('Cannot find a link whose text is %r' % (text,))

    def links_saying(self, text):
        links = anchor_selector(self.tree)
        return [ link for link in links if link.text == text ]

    def text(self, element):
        return ' '.join(
            word
            for text in element.xpath('.//text()')
            for word in text.split()
            )

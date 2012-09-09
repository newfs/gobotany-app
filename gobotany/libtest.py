"""Library of helpers for our tests."""

from django.conf import settings
from django.db import transaction
from django.test.testcases import (
    DEFAULT_DB_ALIAS, TestCase, connections,
    disable_transaction_methods, restore_transaction_methods,
    )
from django.test.client import Client
from psycopg2 import OperationalError
from warnings import warn


Client  # we keep this symbol around so clients can import it easily


class FunctionalCase(TestCase):

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

"""Perform bulk inserts and updates."""

import logging
from collections import defaultdict
log = logging.getLogger('bulkup')

class Database(object):
    def __init__(self, connection):
        self.connection = connection
        self.tabledict = {}

    def map(self, name, key, value=None):
        """Return a dict mapping column `key` to `value` from table `name`."""
        c = self.connection.cursor()
        if value is None:
            c.execute('SELECT {0} FROM {1}'.format(key, name))
            return set(row[0] for row in c.fetchall())
        elif isinstance(key, tuple):
            keylist = ', '.join(key)
            c.execute('SELECT {0}, {1} FROM {2}'.format(keylist, value, name))
            return dict((tuple(row[:-1]), row[-1]) for row in c.fetchall())
        else:
            c.execute('SELECT {0}, {1} FROM {2}'.format(key, value, name))
            return dict(c.fetchall())

    def manymap(self, name, key, value):
        """Return a dict mapping `key` values to a set of `value` values."""
        c = self.connection.cursor()
        r = defaultdict(list)
        c.execute('SELECT {0}, {1} FROM {2}'.format(key, value, name))
        for key, value in c.fetchall():
            r[key].append(value)
        return r

    def table(self, name):
        t = self.tabledict.get(name)
        if t is None:
            t = self.tabledict[name] = Table(self, name)
        return t

class Table(object):
    def __init__(self, database, name):
        self.database = database
        self.name = name
        self.rowdict = {}
        self.keycolumns = None
        self.keycolumnset = None

    def __iter__(self):
        return self.rowdict.itervalues()

    def get(self, **kw):
        keycolumns = list(kw)
        keycolumns.sort()
        if self.keycolumns is None:
            self.keycolumns = keycolumns
            self.keycolumnset = set(kw)
        elif self.keycolumns != keycolumns:
            raise ValueError(
                'please be consistent and always access table {0}'
                ' by the key {1} instead of the key {2}'.format
                (self.name, ','.join(self.keycolumns), ','.join(keycolumns)))
        key = tuple(kw[name] for name in self.keycolumns)
        row = self.rowdict.get(key)
        if row is None:
            row = Row(kw)
            self.rowdict[key] = row
        return row

    def replace(self, attr, mapping):
        """Set ``row.attr`` to the value ``mapping[row.attr]`` for each row."""
        for row in self.rowdict.itervalues():
            d = row.__dict__
            d[attr] = mapping[d[attr]]

        # If rows are indexed by the changed column, then rebuild our index.

        if self.rowdict and (attr in self.keycolumnset):
            rows = self.rowdict.itervalues()
            rowdict = self.rowdict = {}
            for row in rows:
                d = row.__dict__
                key = tuple(d[name] for name in self.keycolumns)
                rowdict[key] = row

    def save(self, delete_old=False):
        if not self.rowdict:
            return
        c = self.database.connection.cursor()
        c.execute('SELECT * FROM {0}'.format(self.name))
        columndict = dict((co[0], i) for (i, co) in enumerate(c.description))
        keycolumnids = [columndict[cn] for cn in self.keycolumns]
        inserts = dict(self.rowdict)
        deletes = []
        with Batch(c, self) as batch:
            for old in c.fetchall():
                key = tuple(old[i] for i in keycolumnids)
                row = inserts.pop(key, None)
                if row is None:
                    if delete_old:
                        deletes.append(key)
                    continue
                writeables = set(row.__dict__.iterkeys()) - self.keycolumnset
                for columnname in writeables:
                    columnno = columndict[columnname]
                    columnvalue = row.__dict__[columnname]
                    if old[columnno] != columnvalue:
                        batch.update(row, writeables, self.keycolumns, key)
                        break
            for row in inserts.values():
                batch.insert(row)
            for key in deletes:
                batch.delete(self.keycolumns, key)

class Row(object):
    def __init__(self, identity):
        self.__dict__.update(identity)

    def set(self, **kw):
        self.__dict__.update(kw)
        return self

    def get(self, field):
        self.__dict__.get(field, None)

class Batch(object):
    def __init__(self, cursor, table, maxlen=10000):
        self.cursor = cursor
        self.table = table
        self.maxlen = maxlen
        self.text = ''
        self.args = []
        self.inserts = self.updates = self.deletes = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if value is not None:  # refuse to flush() on an exception
            return
        self.flush()
        if self.deletes:
            log.info('%s: %s inserts, %s updates, and %s deletes',
                     self.table.name, self.inserts, self.updates, self.deletes)
        else:
            log.info('%s: %s inserts and %s updates',
                     self.table.name, self.inserts, self.updates)

    def insert(self, row):
        self.inserts += 1
        columns = row.__dict__.keys()
        values = row.__dict__.values()
        self.do('INSERT INTO {0} ({1}) VALUES ({2});'
                .format(self.table.name, ','.join(columns),
                        ','.join(['%s'] * len(columns))),
                values)

    def update(self, row, writeables, keycolumns, key):
        self.updates += 1
        values = [ row.__dict__[k] for k in writeables ]
        values.extend(key)
        self.do('UPDATE {0} SET {1} WHERE {2};'.format(
                self.table.name,
                ','.join(s + '= %s' for s in writeables),
                ' AND '.join(s + ' = %s' for s in keycolumns),
                ), values)

    def delete(self, keycolumns, keyvalues):
        self.deletes += 1
        self.do('DELETE FROM {0} WHERE {1};'.format(
                self.table.name,
                ' AND '.join(s + ' = %s' for s in keycolumns)
                ), keyvalues)

    def do(self, text, args):
        self.text += text
        self.args.extend(args)
        if len(self.text) >= self.maxlen:
            self.flush()

    def flush(self):
        # Move parameters into local variables in case we trigger an
        # exception whose cleanup tries to run flush() again.

        text = self.text
        args = self.args
        self.text = ''
        self.args = []
        db_module = self.table.database.connection.settings_dict['ENGINE']
        db_type = db_module.split('.')[3]

        if text:
            if db_type == 'sqlite3':
                self._flush_sqlite(text, args)
            else:
                self.cursor.execute(text, args)

    def _flush_sqlite(self, text, args):
        # sqlite3 doesn't support batching commands, so if we're using that
        # as storage, such as during unit tests, split the commands up
        commands = text.split(';')

        arg_index = 0
        for command in commands:
            arg_count = command.count('%s')
            command_args = args[arg_index:arg_index + arg_count]
            arg_index += arg_count

            self.cursor.execute(command, command_args)


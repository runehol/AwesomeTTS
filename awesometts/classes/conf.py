# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2013-2014  Dave Shifflett
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Storage and management of add-on configuration
"""

# TODO Would it be possible to get these configuration options to sync with
#      AnkiWeb, e.g. by moving them into the collections database?

__all__ = ['Conf']


class Conf(object):
    """
    Exposes a get() and put() method for handling retrieving, caching,
    and serializing configuration information stored in a given SQLite3
    database table.
    """

    __slots__ = [
        '_db',           # path to SQLite3 database
        '_table',        # SQLite3 table where preferences are stored
        '_sanitize',     # regex object for sanitizing names
        '_definitions',  # map of official lookup names to column definitions
        '_cache',        # in-memory lookup of preferences
    ]

    def _normalize(self, name):
        """
        Returns a lowercase version of the name with only characters
        permitted by the sanitization regex object.
        """

        return self._sanitize.sub('', name.lower())

    def __init__(self, db, table, sanitize, definitions):
        """
        Given a database path, table name, and list of column
        definitions, loads the configuration state.

        The column definitions should be a list of tuples, each with:

        - 0th: SQLite3 column name
        - 1st: SQLite3 column affinity
        - 2nd: default Python value to use when introducing new configuration
        - 3rd: mapping function from SQLite3 type to Python type
        - 4th: mapping function from Python type to SQLite3 type
        """

        self._db = db
        self._table = table
        self._sanitize = sanitize
        self._definitions = {
            self._normalize(definition[0]): definition
            for definition
            in definitions
        }

        self._cache = {}
        self._load()

    def _load(self):
        """
        Reads the state of the SQLite3 database to populate our cache.
        If necessary, the database or table will be created with the
        default values. If they already exist, but a new column has been
        added, the already-existing table will be migrated to support
        the new column(s) using the default value(s).
        """

        # open database connection
        import sqlite3
        connection = sqlite3.connect(self._db, isolation_level=None)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        # check for existence of the configuration table
        if len(cursor.execute(
            'SELECT name FROM sqlite_master WHERE type=? AND name=?',
            ('table', self._table),
        ).fetchall()):
            # detect existing columns
            existing_columns = [
                column['name'].lower()
                for column
                in cursor.execute('PRAGMA table_info(%s)' % self._table)
            ]

            # detect any new columns not present in database
            missing_definitions = [
                definition
                for definition
                in self._definitions.values()
                if definition[0].lower() not in existing_columns
            ]

            if missing_definitions:
                # insert any missing columns
                for definition in missing_definitions:
                    cursor.execute('ALTER TABLE %s ADD COLUMN %s %s' % (
                        self._table,
                        definition[0],
                        definition[1],
                    ))

                # set default values for newly-inserted columns
                cursor.execute(
                    'UPDATE %s SET %s' % (
                        self._table,
                        ', '.join([
                            "%s=?" % definition[0]
                            for definition
                            in missing_definitions
                        ]),
                    ),
                    tuple(
                        definition[4](definition[2])
                        for definition
                        in missing_definitions
                    ),
                )

            # populate in-memory store of the values from database
            row = cursor.execute('SELECT * FROM %s' % self._table).fetchone()
            for name, definition in self._definitions.items():
                # attempt to retrieve value; if it fails, use the default
                try:
                    self._cache[name] = definition[3](row[definition[0]])
                except ValueError:
                    self._cache[name] = definition[2]

        else:
            all_definitions = self._definitions.values()

            # create the table
            cursor.execute('CREATE TABLE %s (%s)' % (
                self._table,
                ', '.join([
                    '%s %s' % (definition[0], definition[1])
                    for definition
                    in all_definitions
                ]),
            ))

            # set the default values
            cursor.execute(
                'INSERT INTO %s VALUES(%s)' % (
                    self._table,
                    ', '.join(['?' for definition in all_definitions]),
                ),
                tuple(
                    definition[4](definition[2])
                    for definition
                    in all_definitions
                ),
            )

            # populate in-memory store with the defaults we just inserted
            for name, definition in self._definitions.items():
                self._cache[name] = definition[2]

        # close database connection
        cursor.close()
        connection.close()

    def get(self, name, tokenize=False):
        """
        Retrieve the current value for the given named configuration
        option. The name will be normalized.

        If the caller asks to tokenize the value, it will be cast to a
        string and broken up into a list of words based on delimiting
        whitespace.

        Raises KeyError if the argument is not a supported name.
        """

        value = self._cache[self._normalize(name)]
        return str(value).split() if tokenize else value

    def put(self, **updates):
        """
        Updates the value(s) of the given configuration option(s) passed
        as kwargs-style arguments, and persists those values back to the
        database.

        Raises KeyError if any argument is not a supported name.
        """

        # remap dict into a list of (name, definition, new value)-tuples
        updates = [
            (name, self._definitions[name], value)
            for name, value
            in [
                (self._normalize(unnormalized_name), value)
                for unnormalized_name, value
                in updates.items()
            ]
            if value != self._cache[name]  # filter out unchanged values
        ]

        # return if no updates
        if not updates:
            return

        # update in-memory store of the values
        for name, definition, value in updates:
            self._cache[name] = value

        # open database connection
        import sqlite3
        connection = sqlite3.connect(self._db, isolation_level=None)
        cursor = connection.cursor()

        # persist to SQLite3 database
        cursor.execute(
            'UPDATE %s SET %s' % (
                self._table,
                ', '.join([
                    "%s=?" % definition[0]
                    for name, definition, value
                    in updates
                ]),
            ),
            tuple(
                definition[4](value)
                for name, definition, value
                in updates
            ),
        )

        # close database connection
        cursor.close()
        connection.close()

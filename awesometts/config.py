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
#      AnkiWeb, e.g. by moving them into the collections sqlite database?

__all__ = ['get', 'put']

from re import compile as re
from PyQt4.QtCore import Qt
from .paths import CONFIG_DB


# Name of the table to use in the sqlite3 data for storing configuration

SQLITE_TABLE = 'general'


# Carefully converts sqlite3 value to boolean; this is to handle the
# situation where we might encounter a string from the database driver.
# In which case, bool('0') => True yet TO_BOOL('0') => False.

TO_BOOL = lambda value: bool(int(value))


# Our column definition, list of tuples each containing:
#     0th: sqlite3 column name
#     1st: sqlite3 column affinity
#     2nd: default Python value to use when introducing new configuration
#     3rd: mapping function from sqlite3 type to Python type
#     4th: mapping function from Python type to sqlite3 type

COLUMN_DEFINITIONS = [
    ('automaticAnswers', 'integer', False, TO_BOOL, int),
    ('automaticQuestions', 'integer', False, TO_BOOL, int),
    ('caching', 'integer', True, TO_BOOL, int),
    ('lame_flags', 'text', '--quiet -q 2', str, str),
    ('subprocessing', 'integer', True, TO_BOOL, int),
    ('TTS_KEY_A', 'integer', Qt.Key_F4, Qt.Key, int),
    ('TTS_KEY_Q', 'integer', Qt.Key_F3, Qt.Key, int),
]


# Acceptable aliases for our columns, list of tuples each containing:
#     0th: caller-friendly name of the column
#     1st: official name of column in the sqlite3 database

COLUMN_ALIASES = [
]


def get(name, tokenize=False):  # for linting only, pylint: disable=W0613
    """
    Replaced by get() method from the Config class instance.
    """

    return


def put(**updates):  # for linting only, pylint: disable=W0613
    """
    Replaced by put() method from the Config class instance.
    """

    pass


class Config(object):
    """
    Exposes a get() and put() method for handling retrieving, caching,
    and serializing configuration information stored in a given sqlite3
    database table.
    """

    __name__ = __name__  # enables help() on instance-as-a-module methods

    __slots__ = [
        '_db',           # path to sqlite3 database
        '_table',        # sqlite3 table where preferences are stored
        '_definitions',  # map of official lookup names to column definitions
        '_aliases',      # map of alias lookup names to official lookup names
        '_cache',        # in-memory lookup of preferences
    ]

    # Matches non-alphanumeric characters for normalizing column names
    _RE_NONALPHANUMERIC = re(r'[^a-z0-9]')

    @classmethod
    def _normalize(cls, name):
        """
        Returns a lowercase version of the name with only alphanumeric
        characters.
        """

        return cls._RE_NONALPHANUMERIC.sub('', name.lower())

    def __init__(self, db, table, definitions, aliases):
        """
        Given a database path, table name, list of column definitions,
        and list of column aliases, loads the configuration state.
        """

        self._db = db

        self._table = table

        self._definitions = {
            self._normalize(definition[0]): definition
            for definition
            in definitions
        }

        self._aliases = {
            self._normalize(alias_name): self._normalize(official_name)
            for alias_name, official_name
            in aliases
        }

        self._cache = {}
        self._load()

    def _load(self):
        """
        Reads the state of the sqlite3 database to populate our cache.
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
        option. The name will be normalized and may be an alias.

        If the caller asks to tokenize the value, it will be cast to a
        string and broken up into a list of words based on delimiting
        whitespace.

        Raises KeyError if the argument is not a supported name.
        """

        name = self._normalize(name)

        value = self._cache[
            # check aliases list to see if the passed name is unofficial
            self._aliases[name] if name in self._aliases
            else name
        ]

        return str(value).split() if tokenize else value

    def __getattr__(self, name):
        """
        Alternative to the get() method for backward compatibility.
        """

        try:
            return self.get(name)
        except KeyError:
            raise AttributeError

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
                (
                    name_or_alias if name_or_alias not in self._aliases
                    else self._aliases[name_or_alias],
                    value,
                )
                for name_or_alias, value
                in [
                    (self._normalize(unnormalized_name_or_alias), value)
                    for unnormalized_name_or_alias, value
                    in updates.items()
                ]
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

        # persist to sqlite3 database
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


from sys import modules

modules[__name__] = Config(
    CONFIG_DB,
    SQLITE_TABLE,
    COLUMN_DEFINITIONS,
    COLUMN_ALIASES,
)

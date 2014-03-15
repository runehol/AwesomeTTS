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
# TODO Double-check all migration pathways for correct behavior

__all__ = [
    'get',
    'put',
]

from re import compile as re
from PyQt4.QtCore import Qt
from .paths import CONFIG_DB


SQLITE_TABLE = 'general'

COLUMN_DEFINITIONS = [
    # column, type, default, sqlite-to-Python mapper, Python-to-sqlite mapper
    ('automaticAnswers', 'integer', 0, bool, int),
    ('automaticQuestions', 'integer', 0, bool, int),
    ('caching', 'integer', 1, bool, int),
    ('file_howto_name', 'integer', 1, bool, int),
    ('subprocessing', 'integer', 1, bool, int),
    ('TTS_KEY_A', 'integer', Qt.Key_F4, Qt.Key, int),
    ('TTS_KEY_Q', 'integer', Qt.Key_F3, Qt.Key, int),
]

COLUMN_ALIASES = [
    # caller-friendly name to database name
    ('quote_mp3', 'file_howto_name'),
]


def get(dummy):
    """
    Replaced by get method from the Config class instance.
    """

    return


def put(**dummy):
    """
    Replaced by put method from the Config class instance.
    """

    pass


class Config(object):
    __slots__ = [
        '_db',           # path to sqlite3 database
        '_table',        # sqlite3 table where preferences are stored
        '_definitions',  # map of official lookup names to column definitions
        '_aliases',      # map of alias lookup names to official lookup names
        '_cache',        # in-memory lookup of preferences
    ]

    _RE_NONALPHANUMERIC = re(r'[^a-z0-9]')

    @classmethod
    def _normalize(cls, name):

        return cls._RE_NONALPHANUMERIC.sub('', name.lower())

    def __init__(self, db, table, definitions, aliases):

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

        import sqlite3
        connection = sqlite3.connect(self._db, isolation_level=None)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if len(cursor.execute(
            'SELECT name FROM sqlite_master WHERE type=? AND name=?',
            ('table', self._table),
        ).fetchall()):
            existing_columns = [
                column['name'].lower()
                for column
                in cursor.execute('PRAGMA table_info(%s)' % self._table)
            ]

            missing_definitions = [
                definition
                for definition
                in self._definitions.values()
                if definition[0].lower() not in existing_columns
            ]

            if missing_definitions:
                for definition in missing_definitions:
                    cursor.execute('ALTER TABLE %s ADD COLUMN %s %s' % (
                        self._table,
                        definition[0],
                        definition[1],
                    ))

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

        else:
            all_definitions = self._definitions.values()

            cursor.execute('CREATE TABLE %s (%s)' % (
                self._table,
                ', '.join([
                    '%s %s' % (definition[0], definition[1])
                    for definition
                    in all_definitions
                ]),
            ))

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

        row = cursor.execute('SELECT * FROM %s' % self._table).fetchone()
        for name, definition in self._definitions.items():
            self._cache[name] = definition[3](row[definition[0]])

        cursor.close()
        connection.close()

    def get(self, name):

        name = self._normalize(name)
        return self._cache[
            self._aliases[name] if name in self._aliases
            else name
        ]

    def put(self, **updates):

        # remap dict into a list of (name, definition, new value)-tuples
        updates = [
            (
                name,
                self._definitions[name],
                value,
            )
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

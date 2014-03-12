# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2014       Dave Shifflett
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

# TODO Specify configuration slots with a data structure
# TODO Make a way to migrate keys, needed for file_howto_name -> quote_mp3
# TODO Can/should we be using the "with" statement with the sqlite connection?
# TODO Based on the data structure, add code paths to automatically...
#          - create and populate configuration table when none exists
#          - add new configuration slots to table
#          - remove disused configuration slots from table
# TODO Fix saving (it looks like the passed parameter is this module itself)
# TODO Simplify interface, e.g.
#          - get (maybe overloaded for get all)
#          - set (maybe overloaded for set many)
# TODO Correctly advertise interface with __all__

from os import path
import sqlite3
from sys import getfilesystemencoding as fs_encoding

from PyQt4.QtCore import Qt


ADDON_DIRECTORY = path.dirname(path.realpath(__file__))
CACHE_DIRECTORY = path.join(ADDON_DIRECTORY, 'cache').decode(fs_encoding())
SQLITE_PATH = path.join(ADDON_DIRECTORY, 'conf.db').decode(fs_encoding())

conn = sqlite3.connect(SQLITE_PATH, isolation_level=None)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='general'")

if len(cursor.fetchall()) < 1:
    cursor.execute(
        "CREATE TABLE general ("
            "automaticQuestions numeric,"
            "automaticAnswers numeric,"
            "file_howto_name numeric,"
            "subprocessing numeric,"
            "TTS_KEY_Q numeric,"
            "TTS_KEY_A numeric,"
            "caching numeric"
        ")"
    )
    cursor.execute(
        "INSERT INTO general "
        "VALUES (0, 0, 1, 1, ?, ?, 1)",
        (Qt.Key_F3, Qt.Key_F4)
    )

else:
    cursor.execute("PRAGMA table_info(general)")
    for r in cursor:
        if r['name'] == 'caching':
            break
    else:
        cursor.execute(
            "ALTER TABLE general "
            "ADD COLUMN caching numeric DEFAULT 1"
        )

cursor.execute("SELECT * FROM general")

r = cursor.fetchone()


# Key to get the [TTS::] tags in the Question field pronounced
TTS_KEY_Q=r['TTS_KEY_Q']

# Key to get the [TTS::] tags in the Answer field pronounced
TTS_KEY_A=r['TTS_KEY_A']


automaticQuestions = r['automaticQuestions']
automaticAnswers = r['automaticAnswers']
quote_mp3 = r['file_howto_name']
subprocessing = r['subprocessing']

caching = r['caching']
cachingDirectory = CACHE_DIRECTORY

def saveConfig(config):
    cursor.execute(
        "UPDATE general SET "
        "automaticQuestions=?, automaticAnswers=?,"
        "file_howto_name=?,"
        "subprocessing=?,"
        "TTS_KEY_Q=?, TTS_KEY_A=?, caching=?",
        (config.automaticQuestions, config.automaticAnswers,
         config.quote_mp3,
         config.subprocessing,
         config.TTS_KEY_Q, config.TTS_KEY_A, config.caching)
    )


TTS_service = {}

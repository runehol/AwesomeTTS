# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2013  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2013       Dave Shifflett
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


from PyQt4.QtCore import *
import os, sys, sqlite3

conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "conf.db")
conffile = conffile.decode(sys.getfilesystemencoding())
 
conn = sqlite3.connect(conffile, isolation_level=None)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='general'")

tblexit = cursor.fetchall()


if len (tblexit) < 1:
	cursor.execute(
		"CREATE TABLE general ("
			"automaticQuestions numeric,"
			"automaticAnswers numeric,"
			"file_howto_name numeric,"
			"file_max_length numeric,"
			"file_extension text,"
			"subprocessing numeric,"
			"TTS_KEY_Q numeric,"
			"TTS_KEY_A numeric,"
			"caching numeric"
		")"
	)
	cursor.execute(
		"INSERT INTO general "
		"VALUES (0, 0, 1, 100, 'mp3', 1, ?, ?, 1)",
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
file_max_length = r['file_max_length']
file_extension = r['file_extension']

caching = r['caching']
cachingDirectory = os.path.sep.join([
	os.path.dirname(__file__),
	'cache'
])

def saveConfig(config):
	cursor.execute(
		"UPDATE general SET "
		"automaticQuestions=?, automaticAnswers=?,"
		"file_howto_name=?, file_max_length=?,"
		"file_extension=?, subprocessing=?,"
		"TTS_KEY_Q=?, TTS_KEY_A=?, caching=?",
		(config.automaticQuestions, config.automaticAnswers,
		 config.quote_mp3, config.file_max_length,
		 config.file_extension, config.subprocessing,
		 config.TTS_KEY_Q, config.TTS_KEY_A, config.caching)
	)


TTS_service = {}

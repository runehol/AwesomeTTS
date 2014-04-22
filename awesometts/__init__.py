# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2013  Arthur Helfstein Fragoso
# Copyright (C) 2013-2014  Dave Shifflett
# Copyright (C) 2012       Dominic Lerbs
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
Add-on package initialization
"""

# We expose instances here used across the add-on, pylint: disable=C0103

__all__ = [
    'conf',
    'logger',
    'router',
]

import json
import logging
from sys import stdout
from PyQt4.QtCore import Qt
from . import classes, paths, regex


_TO_BOOL = lambda value: bool(int(value))  # workaround for bool('0') == True

_TO_NORMALIZED = lambda value: ''.join(
    char.lower()
    for char in value
    if char.isalpha() or char.isdigit()
)


logger = classes.Logger(
    name='AwesomeTTS',

    handlers={
        'debug_file': logging.FileHandler(
            paths.ADDON_LOG,
            encoding='utf-8',
            delay=True,
        ),
        'debug_stdout': logging.StreamHandler(stdout),
    },

    formatter=logging.Formatter(
        '[%(asctime)s %(module)s@%(lineno)d %(levelname)s] %(message)s',
        '%H:%M:%S',
    ),
)


conf = classes.Conf(
    db=(paths.CONF_DB, 'general', _TO_NORMALIZED),

    definitions=[
        ('automaticAnswers', 'integer', False, _TO_BOOL, int),
        ('automaticQuestions', 'integer', False, _TO_BOOL, int),
        ('debug_file', 'integer', False, _TO_BOOL, int),
        ('debug_stdout', 'integer', False, _TO_BOOL, int),
        ('lame_flags', 'text', '--quiet -q 2', str, str),
        ('last_mass_dest', 'text', 'Back', str, str),
        ('last_mass_source', 'text', 'Front', str, str),
        ('last_service', 'text', 'google', str, str),
        ('last_options', 'text', {}, json.loads, json.dumps),
        ('TTS_KEY_A', 'integer', Qt.Key_F4, Qt.Key, int),
        ('TTS_KEY_Q', 'integer', Qt.Key_F3, Qt.Key, int),
    ],

    logger=logger,

    events=[
        (
            ['debug_file', 'debug_stdout'],
            logger.activate,  # BufferedLogger instance, pylint: disable=E1103
        ),
    ],
)

router = classes.Router(
    services=dict(
        mappings=[
            ('ekho', classes.services.Ekho),
            ('espeak', classes.services.ESpeak),
            ('google', classes.services.Google),
            ('sapi5', classes.services.SAPI5),
            ('say', classes.services.Say),
        ],

        aliases=[
            ('g', 'google'),
        ],

        normalize=_TO_NORMALIZED,
    ),

    paths=dict(
        cache=paths.CACHE_DIR,
        temp=paths.TEMP_DIR,
    ),

    conf=conf,

    logger=logger,
)

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
]

from PyQt4.QtCore import Qt
from . import classes, paths, regex, util


conf = classes.Conf(
    db=paths.CONF_DB,
    table='general',
    sanitize=regex.NOT_ALPHANUMERIC,
    definitions=[
        ('automaticAnswers', 'integer', False, util.TO_BOOL, int),
        ('automaticQuestions', 'integer', False, util.TO_BOOL, int),
        ('caching', 'integer', True, util.TO_BOOL, int),
        ('lame_flags', 'text', '--quiet -q 2', str, str),
        ('subprocessing', 'integer', True, util.TO_BOOL, int),
        ('TTS_KEY_A', 'integer', Qt.Key_F4, Qt.Key, int),
        ('TTS_KEY_Q', 'integer', Qt.Key_F3, Qt.Key, int),
    ],
)

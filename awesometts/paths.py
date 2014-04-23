# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2012-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2012       Arthur Helfstein Fragoso
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
Helpers for accessing directories and files

The constants exposed by this module are relative to the add-on's "code
directory", which is the directory containing paths.py (among others).
"""

__all__ = [
    'ADDON_LOG',
    'CACHE_DIR',
    'CONFIG_DB',
    'TEMP_DIR',
]

import os
import os.path


# When determining the code directory, abspath() is needed since the
# __file__ constant is not a full path by itself.

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))


ADDON_LOG = os.path.join(_CODE_DIR, 'addon.log')

CACHE_DIR = os.path.join(_CODE_DIR, 'cache')

if not os.path.isdir(CACHE_DIR):
    os.mkdir(CACHE_DIR)

CONFIG_DB = os.path.join(_CODE_DIR, 'config.db')

TEMP_DIR = os.path.join(_CODE_DIR, 'temp')

if not os.path.isdir(TEMP_DIR):
    os.mkdir(TEMP_DIR)

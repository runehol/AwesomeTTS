# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2013-2014  Anki AwesomeTTS Development Team
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
Helpful type conversions
"""

__all__ = ['BOOL', 'NULLABLE_INT', 'NULLABLE_KEY', 'JSON_DICT', 'NORMALIZED']

import json

from PyQt4.QtCore import Qt


BOOL = lambda value: bool(int(value))  # workaround for bool('0') == True

NULLABLE_INT = lambda value: int(value) if value else None

NULLABLE_KEY = lambda value: Qt.Key(value) if value else None

JSON_DICT = lambda value: isinstance(value, basestring) and \
    value.lstrip().startswith('{') and json.loads(value) or {}

NORMALIZED = lambda value: ''.join(
    char.lower()
    for char in value
    if char.isalpha() or char.isdigit()
)

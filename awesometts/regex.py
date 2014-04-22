# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2014       Anki AwesomeTTS Development Team
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
Helpful regular expression patterns
"""

__all__ = [
    'NOT_ALPHANUMERIC',
    'SOUND_BRACKET_TAG',
    'WHITESPACE',
]

import re


# Filter pattern to remove non-alphanumeric characters
NOT_ALPHANUMERIC = re.compile(r'[^a-zA-Z0-9]')

# Matches [sound:xxx]-style Tags
SOUND_BRACKET_TAG = re.compile(r'\[sound:[^\]]+\]', re.IGNORECASE)

# Filter pattern to collapse whitespace
WHITESPACE = re.compile(r'\s+')

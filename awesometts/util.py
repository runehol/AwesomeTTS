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
Utility module

Stuff that does not fit anywhere else.
"""

__all__ = [
    'STARTUP_INFO',  # Windows only
    'TO_BOOL',
    'TO_HEXSTR',
]

import subprocess


# Startup information for Windows only; None on other platforms

STARTUP_INFO = None

if subprocess.mswindows:
    # initialize startup information object
    STARTUP_INFO = subprocess.STARTUPINFO()
    try:
        STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except AttributeError:  # workaround for some Python implementations
        STARTUP_INFO.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW


# Carefully convert an unknown value to a boolean; this is to handle the
# situation where we convert from a string. So, TO_BOOL('0') => False
# as one might expect, but bool('0') => True, as one might not expect.

TO_BOOL = lambda value: bool(int(value))


# Returns the 8-bit string version of a unicode string

TO_ENCODED = lambda s: s.encode('utf-8') if isinstance(s, unicode) else s


# Returns a hexadecimal string representation of what is passed.

TO_HEXSTR = lambda value: ''.join(['%04X' % ord(char) for char in value])


# Returns a list of string tokens from a passed string.

TO_TOKENS = lambda value: str(value).split()

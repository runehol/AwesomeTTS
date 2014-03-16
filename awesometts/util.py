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
Processes and operating system details
"""

# TODO Switch over other modules to the new interfaces.

__all__ = [
    'hex_string',
    'STARTUP_INFO',    # Windows only
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


def hex_string(src):
    """
    Returns a hexadecimal string representation of what is passed.
    """

    return ''.join(['%04X' % ord(x) for x in src])


# backward-compatibility section follows, pylint: disable=C0103,W0613

def generateFileName(text, service, winencode='iso-8859-1', extention='.mp3'):
    """
    Old function name and call signature, replaced by media_filename()
    in the paths module.
    """

    from .paths import media_filename
    return media_filename(
        text,
        service,
        extension=extention,
    )

dumpUnicodeStr = hex_string

si = STARTUP_INFO

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

# TODO The filename-related stuff should probably move to the paths module
# TODO The awkwardness of the quoted filenames really shows why a hashed
#      filename solution is necessary
# TODO Switch over other modules to the new interfaces.

__all__ = [
    'media_filename',
    'hex_string',
    'STARTUP_INFO',    # Windows only
]

import os
from re import compile as re
import subprocess
from sys import argv
from urllib import quote_plus
import awesometts.config as config


# Max filename length for Unix; set below for Windows
FILE_MAX_LENGTH = 255

# Filter pattern to remove dangerous characters from filenames: \/:*?"<>|[]
RE_UNSAFE_CHARACTERS = re(r'[\\\/\:\*\?"<>|\[\]\.]*')

# Startup information for Windows only; None on other platforms
STARTUP_INFO = None

if subprocess.mswindows:
    # guess filename max length for Windows (where path + filename <= 255)
    FILE_MAX_LENGTH = 100

    # enable mplayer binary to be called in the path
    os.environ['PATH'] += ";" + os.path.dirname(os.path.abspath(argv[0]))

    # initialize startup information object
    STARTUP_INFO = subprocess.STARTUPINFO()
    try:
        STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except AttributeError:  # Python 2.7+
        STARTUP_INFO.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW


def media_filename(
    text, service, voice=None,
    win_encode='iso-8859-1', extension='.mp3',
):
    """
    Given the user's preferences about filenames, return a usable media
    filename given the passed text, service, and voice. Attempts to
    correct for encoding.
    """

    name = "%s by %s %s" % (
        RE_UNSAFE_CHARACTERS.sub('', text),
        service,
        voice or 'voice',
    )

    if config.get('quote_mp3'):
        name = quote_plus(name).replace('%', '') + extension

        if len(name) > FILE_MAX_LENGTH:
            name = name[0:FILE_MAX_LENGTH - len(extension)] + extension

    else:
        name = name + extension

        if len(name) > FILE_MAX_LENGTH:
            name = name[0:FILE_MAX_LENGTH - len(extension)] + extension

        if subprocess.mswindows:
            name = name.decode('utf-8').encode(win_encode)

    return name


def hex_string(src):
    """
    Returns a hexadecimal string representation of what is passed.
    """

    return ''.join(['%04X' % ord(x) for x in src])


# backward-compatibility section follows, pylint: disable=C0103

def generateFileName(text, service, winencode='iso-8859-1', extention=".mp3"):
    """
    Old function name and call signature media_filename().
    """

    return media_filename(
        text,
        service,
        win_encode=winencode,
        extension=extention,
    )

dumpUnicodeStr = hex_string

si = STARTUP_INFO

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
# TODO Presumably the same fs encoding fixes from the paths module need to
#      be applied to the logic of media_filename
# TODO The awkwardness of the quoted filenames really shows why a hashed
#      filename solution is necessary
# TODO Switch over other modules to the new interfaces.

__all__ = [
    'media_filename',
    'hex_string',
    'STARTUP_INFO',    # Windows only
]

from hashlib import md5
import os
from re import compile as re
import subprocess
from sys import argv


# Filter pattern to remove non-alphanumeric and non-dash characters
RE_NONDASHEDALPHANUMERIC = re(r'[^-a-z0-9]')

# Filter pattern to collapse whitespace
RE_WHITESPACE = re(r'\s+')

# Startup information for Windows only; None on other platforms
STARTUP_INFO = None

if subprocess.mswindows:
    # enable mplayer binary to be called in the path
    os.environ['PATH'] += ";" + os.path.dirname(os.path.abspath(argv[0]))

    # initialize startup information object
    STARTUP_INFO = subprocess.STARTUPINFO()
    try:
        STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except AttributeError:  # Python 2.7+
        STARTUP_INFO.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW


def media_filename(text, service, voice=None, extension='mp3'):
    """
    Return a usable media filename given the passed text, service,
    voice, and extension.
    """

    def normalize_identifier(source):
        """
        Return a lowercase version of the string with only alphanumeric
        characters and intermediate dashes.
        """

        return RE_NONDASHEDALPHANUMERIC.sub('', source.lower()).strip('-')

    def hash_phrase(source):
        """
        Return an MD5-hashed version of a string normalized to lowercase
        with any whitespace collapsed and stripped off.
        """

        return md5(RE_WHITESPACE.sub(' ', source).strip()).hexdigest().lower()

    return (
        "%s-%s-%s.%s" % (
            normalize_identifier(service),
            normalize_identifier(voice),
            hash_phrase(text),
            normalize_identifier(extension),
        ) if voice
        else "%s-%s.%s" % (
            normalize_identifier(service),
            hash_phrase(text),
            normalize_identifier(extension),
        )
    )


def hex_string(src):
    """
    Returns a hexadecimal string representation of what is passed.
    """

    return ''.join(['%04X' % ord(x) for x in src])


# backward-compatibility section follows, pylint: disable=C0103,W0613

def generateFileName(text, service, winencode='iso-8859-1', extention='.mp3'):
    """
    Old function name and call signature replaced by media_filename().
    """

    return media_filename(
        text,
        service,
        extension=extention.strip('.'),
    )

dumpUnicodeStr = hex_string

si = STARTUP_INFO

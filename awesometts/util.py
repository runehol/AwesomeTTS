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
# TODO The regex stuff should probably move to a new patterns module
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


# Filter pattern to remove non-alphanumeric characters
RE_NONALPHANUMERIC = re(r'[^a-z0-9]')

# Filter pattern to remove non-alphanumeric and non-dash characters
RE_NONDASHEDALPHANUMERIC = re(r'[^-a-z0-9]')

# Filter pattern to remove non-alphanumeric and non-period characters
RE_NONDOTTEDALPHANUMERIC = re(r'[^\.a-z0-9]')

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
    voice, and extension. If the voice is omitted, it will also be
    omitted from the resulting filename.
    """

    text = RE_WHITESPACE.sub(' ', text).strip()
    md5text = md5(text).hexdigest().lower()
    service = RE_NONALPHANUMERIC.sub('', service.lower())
    extension = RE_NONDOTTEDALPHANUMERIC.sub('', extension.lower()).strip('.')

    if voice:
        voice = RE_NONDASHEDALPHANUMERIC.sub('', voice.lower()).strip('-')
        return "%s-%s-%s.%s" % (service, voice, md5text, extension)

    else:
        return "%s-%s.%s" % (service, md5text, extension)


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
        extension=extention,
    )

dumpUnicodeStr = hex_string

si = STARTUP_INFO

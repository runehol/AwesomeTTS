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
These are derived using the module's relative() helper function, which
can also be used in other modules for easily formulating full paths to
individual files.
"""

__all__ = [
    'relative',
    'cache_path',
    'temp_path',
    'ADDON_LOG',
    'CACHE_DIR',
    'CONF_DB',
    'TEMP_DIR',
]

from os import environ, mkdir
from os.path import abspath, dirname, exists, isdir
from subprocess import mswindows
from sys import argv


# Determine the Anki binary's directory. On Linux and Mac OS X, this is
# not particularly interesting, but on Windows, this directory will also
# contain the lame.exe and mplayer.exe binaries.

_ANKI_DIR = dirname(abspath(argv[0]))

if mswindows:
    environ['PATH'] += ';' + _ANKI_DIR


# When determining the code directory, abspath() is needed since the
# __file__ constant is not a full path by itself.

_CODE_DIR = dirname(abspath(__file__))


def relative(start_dir, to_path, *addl_paths):
    """
    Returns the full path to a file or directory relative to the given
    start directory, using the operating system's path separator.
    Multiple path components may be passed.

    While the path will be normalized, any symlink on the file system is
    returned as-is (e.g. a child directory that is actually a symlink
    will not be resolved to its target path).
    """

    from os.path import join, normpath

    components = [start_dir, to_path] + list(addl_paths)

    return normpath(
        join(*components)  # join() takes *args, pylint: disable=W0142
    )


ADDON_LOG = relative(_CODE_DIR, 'addon.log')

CACHE_DIR = relative(_CODE_DIR, 'cache')

if not isdir(CACHE_DIR):
    mkdir(CACHE_DIR)

CONF_DB = relative(_CODE_DIR, 'conf.db')

SERVICES_DIR = relative(_CODE_DIR, 'services')

TEMP_DIR = relative(_CODE_DIR, 'temp')

if not isdir(TEMP_DIR):
    mkdir(TEMP_DIR)

WINDOWS_DIR = next(
    (
        directory
        for directory in [
            environ.get('SYSTEMROOT', None),
            r'C:\Windows',
            r'C:\WinNT',
        ]
        if directory and exists(directory)
    ),
    None
) if mswindows else None


def _get_path(directory, text, service, voice=None, extension='mp3'):
    """
    Return a portable path given the passed directory, text, service,
    optional voice, and extension. If voice is omitted, it will also be
    omitted from the resulting path. If extension is omitted, it will
    default to MP3.
    """

    from hashlib import md5
    from .util import TO_ENCODED
    from . import regex as re

    text = re.WHITESPACE.sub(' ', text).strip()
    encoded = TO_ENCODED(text)
    md5text = md5(encoded).hexdigest().lower()

    service = re.NOT_ALPHANUMERIC.sub('', service.lower())
    extension = re.NOT_ALPHANUMERIC_DOT.sub('', extension.lower()).strip('.')

    if voice:
        voice = re.NOT_ALPHANUMERIC_DASH.sub('', voice.lower()).strip('-')
        filename = "%s-%s-%s.%s" % (service, voice, md5text, extension)

    else:
        filename = "%s-%s.%s" % (service, md5text, extension)

    return relative(directory, filename)

def cache_path(*args, **kwargs):
    """
    Return a portable cache path.
    """

    return _get_path(CACHE_DIR, *args, **kwargs)

def temp_path(*args, **kwargs):
    """
    Return a portable temporary path.
    """

    return _get_path(TEMP_DIR, *args, **kwargs)

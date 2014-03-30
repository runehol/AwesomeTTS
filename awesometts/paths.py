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
    'media_filename',
    'relative',
    'ADDON_LOG',
    'CACHE_DIR',
    'CONF_DB',
]

from hashlib import md5
from os import mkdir
from os.path import (
    abspath,
    dirname,
    isdir,
    join,
    normpath,
)
from subprocess import mswindows
from sys import (
    argv,
    getfilesystemencoding,
)
from . import regex as re


# Set the encoding type we should use for all path and filename strings.

_ENCODING = getfilesystemencoding()


# Determine the Anki binary's directory. On Linux and Mac OS X, this is
# not particularly interesting, but on Windows, this directory will also
# contain the mplayer.exe binary.
#
# Note that the decode() call is deferred until after the PATH setup for
# Windows. This is done so as to not convert the PATH value from a
# regular string to a unicode one.

_ANKI_DIR = dirname(abspath(argv[0]))

if mswindows:
    # Enable mplayer.exe binary to be called from the environment PATH.
    from os import environ
    environ['PATH'] += ';' + _ANKI_DIR

_ANKI_DIR = _ANKI_DIR.decode(_ENCODING)


# When determining the code directory, abspath() is needed since the
# __file__ constant is not a full path by itself.

_CODE_DIR = dirname(abspath(__file__)).decode(_ENCODING)


def relative(start_dir, to_path, *addl_paths):
    """
    Returns the full path to a file or directory relative to the given
    start directory, using the operating system's path separator and
    file system encoding. Multiple path components may be passed.

    While the path will be normalized, any symlink on the file system is
    returned as-is (e.g. a child directory that is actually a symlink
    will not be resolved to its target path).
    """

    components = [start_dir, to_path] + list(addl_paths)

    return normpath(
        join(*components)  # join() takes *args, pylint: disable=W0142
    ).decode(_ENCODING)


ADDON_LOG = relative(_CODE_DIR, 'addon.log')

CACHE_DIR = relative(_CODE_DIR, 'cache')

if not isdir(CACHE_DIR):
    mkdir(CACHE_DIR)

CONF_DB = relative(_CODE_DIR, 'conf.db')


def media_filename(text, service, voice=None, extension='mp3'):
    """
    Return a portable media filename using the operating system's file
    system encoding given the passed text, service, optional voice, and
    extension. If voice is omitted, it will also be omitted from the
    resulting filename. If extension is omitted, it will default to MP3.
    """

    text = re.WHITESPACE.sub(' ', text).strip()
    md5text = md5(text).hexdigest().lower()
    service = re.NOT_ALPHANUMERIC.sub('', service.lower())
    extension = re.NOT_ALPHANUMERIC_DOT.sub('', extension.lower()).strip('.')

    if voice:
        voice = re.NOT_ALPHANUMERIC_DASH.sub('', voice.lower()).strip('-')
        filename = "%s-%s-%s.%s" % (service, voice, md5text, extension)

    else:
        filename = "%s-%s.%s" % (service, md5text, extension)

    return filename.decode(_ENCODING)

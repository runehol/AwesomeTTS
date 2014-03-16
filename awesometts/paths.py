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

# TODO Presumably the same fs encoding fixes from the paths module need to
#      be applied to the logic of media_filename

__all__ = [
    'media_filename',
    'relative',
    'CACHE_DIR',
    'CONFIG_DB',
]

from hashlib import md5
from os.path import (
    dirname,
    join,
    normpath,
    realpath,
)
from sys import getfilesystemencoding
from . import regex as re


_ENCODING = getfilesystemencoding()


# When determining the code directory, realpath() is needed since the
# __file__ constant is not a full path by itself. However, this is done
# using realpath(dirname(...)) rather than dirname(realpath(...)) to
# correctly handle the edge case of there being a paths.py symlink in
# the code directory pointing to the physical source file living
# somewhere else on the file system.

_CODE_DIR = realpath(dirname(__file__)).decode(_ENCODING)


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


CACHE_DIR = relative(_CODE_DIR, 'cache')

CONFIG_DB = relative(_CODE_DIR, 'conf.db')


def media_filename(text, service, voice=None, extension='mp3'):
    """
    Return a usable media filename given the passed text, service,
    voice, and extension. If the voice is omitted, it will also be
    omitted from the resulting filename.
    """

    text = re.WHITESPACE.sub(' ', text).strip()
    md5text = md5(text).hexdigest().lower()
    service = re.NOT_ALPHANUMERIC.sub('', service.lower())
    extension = re.NOT_ALPHANUMERIC_DOT.sub('', extension.lower()).strip('.')

    if voice:
        voice = re.NOT_ALPHANUMERIC_DASH.sub('', voice.lower()).strip('-')
        return "%s-%s-%s.%s" % (service, voice, md5text, extension)

    else:
        return "%s-%s.%s" % (service, md5text, extension)

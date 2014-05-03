# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2013  Arthur Helfstein Fragoso
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
#
# Instructions on the AnkiWeb at <https://ankiweb.net/shared/info/301952613>.
# Problems or comments? Visit <https://github.com/AwesomeTTS/AwesomeTTS>.

"""
Entry point for AwesomeTTS add-on from Anki

Performs any needed migration tasks (e.g. renaming conf.db to config.db,
removal of old modules and packages, removal of other unneeded files),
then loads the 'awesometts' package to bootstrap the add-on.
"""

__all__ = []


if __name__ == "__main__":
    from sys import stderr

    stderr.write(
        "AwesomeTTS is a text-to-speech add-on for Anki.\n"
        "It is not intended to be run directly.\n"
        "To learn more or download Anki, please visit <http://ankisrs.net>.\n"
    )
    exit(1)


# Begin temporary migration code from Beta 10 and older

import os

def os_call(callee, *args, **kwargs):
    """Call the function with the given arguments, ignoring OSError."""

    try:
        callee(*args, **kwargs)
    except OSError:
        pass

_PKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'awesometts')

for _filename in [
    'main.py', 'main.pyc', 'main.pyo',
    'util.py', 'util.pyc', 'util.pyo',
]:
    os_call(os.unlink, os.path.join(_PKG, _filename))

for _directory, _filenames in [
    ('designer', [
        'configurator.ui', 'filegenerator.ui', 'massgenerator.ui',
    ]),
    ('forms', [
        'configurator.py', 'configurator.pyc', 'configurator.pyo',
        'filegenerator.py', 'filegenerator.pyc', 'filegenerator.pyo',
        'massgenerator.py', 'massgenerator.pyc', 'massgenerator.pyo',
        '__init__.py', '__init__.pyc', '__init__.pyo',
    ]),
    ('services', [
        'ekho.py', 'ekho.pyc', 'ekho.pyo',
        'espeak.py', 'espeak.pyc', 'espeak.pyo',
        'Google.py', 'Google.pyc', 'Google.pyo',
        'sapi5.py', 'sapi5.pyc', 'sapi5.pyo', 'sapi5.vbs',
        'say.py', 'say.pyc', 'say.pyo',
        '__init__.py', '__init__.pyc', '__init__.pyo',
    ]),
    ('tools', [
        'build_ui.sh',
    ]),
]:
    for _filename in _filenames:
        os_call(os.unlink, os.path.join(_PKG, _directory, _filename))

    os_call(os.rmdir, os.path.join(_PKG, _directory))

os_call(
    os.rename,
    os.path.join(_PKG, 'conf.db'),
    os.path.join(_PKG, 'config.db'),
)

# End temporary migration code


import awesometts  # imported for side effects, pylint: disable=W0611

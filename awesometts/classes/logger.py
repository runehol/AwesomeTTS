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
Logger support across entire add-on
"""

__all__ = ['Logger']

import logging


def Logger(  # factory masquerading as a constructor, pylint: disable=C0103
    name,
    stdout_flag, file_flag, file_path,
):
    """
    Returns a logger with the given name after configuring it. If called
    again with the same name, the same logger will be returned, but its
    configuration will be updated.

    See the BufferedLogger configure() method for more information.
    """

    default_cls = logging.getLoggerClass()

    logging.setLoggerClass(BufferedLogger)
    new_instance = logging.getLogger(name)
    logging.setLoggerClass(default_cls)

    new_instance.configure(  # will be a BufferedLogger, pylint: disable=E1103
        stdout_flag,
        file_flag,
        file_path,
    )
    return new_instance


class BufferedLogger(logging.Logger):  # many inherited, pylint: disable=R0904
    """
    Extends the built-in logger to support buffered logs, i.e. logs that
    can be written to before handlers are setup. This is handy for when
    we don't know until later in program execution whether the user even
    wants logging to take place.
    """

    __slots__ = [
        '_activated',    # True if we are activated, False otherwise
        '_buffer',       # log messages that come in before activation
        '_stdout_flag',  # key to look for in activate() call for stdout
        '_file_flag',    # key to look for in activate() call for file output
        '_file_path',    # path to a log file for use if activated
    ]

    def __init__(self, *args, **kwargs):
        """
        Note that because we do not call this directly and instead the
        logging module does the calling and only knows about names, some
        setup is deferred to the configure() method. If calling code
        uses the Logger factory function defined at the module level,
        this will be called automatically.
        """

        super(BufferedLogger, self).__init__(*args, **kwargs)
        self._activated = False
        self._buffer = []
        self._stdout_flag = None
        self._file_flag = None
        self._file_path = None

    def configure(self, stdout_flag, file_flag, file_path):
        """
        Configures the flags that will trigger the logger to use stdout
        and file-based logging. Additionally, configures the logging
        path to be used.
        """

        self._stdout_flag = stdout_flag
        self._file_flag = file_flag
        self._file_path = file_path

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
from sys import stdout


def Logger(  # factory masquerading as a constructor, pylint: disable=C0103
    name,
    stdout_flag, file_flag, file_path, file_encoding,
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
        file_encoding,
    )
    return new_instance


class BufferedLogger(logging.Logger):  # lots inherited, pylint: disable=R0904
    """
    Extends the built-in logger to support buffered logs, i.e. logs that
    can be written to before handlers are setup. This is handy for when
    we don't know until later in program execution whether the user even
    wants logging to take place.
    """

    __slots__ = [
        '_activated',    # True if we are activated, False otherwise
        '_buffer',       # list of log messages that come in before activation
        '_stdout_flag',  # key to look for in activate() call for stdout
        '_stdout_sh',    # StreamHandler to stdout; always initialized
        '_file_flag',    # key to look for in activate() call for file output
        '_file_fh',      # FileHandler for log file; delayed initialization
    ]

    def __init__(self, *args, **kwargs):
        """
        Note that because we do not call this directly and instead the
        logging module does the calling and only knows about names, some
        setup is deferred until the configure() method. If calling code
        uses the Logger factory function defined at the module level,
        this will be called automatically.
        """

        super(BufferedLogger, self).__init__(*args, **kwargs)
        self._activated = False
        self._buffer = []
        self._stdout_flag = None
        self._stdout_sh = logging.StreamHandler(stdout)
        self._file_flag = None
        self._file_fh = None

    def configure(self, stdout_flag, file_flag, file_path, file_encoding):
        """
        Configures the flags that will trigger the logger to use stdout
        and file-based logging. Additionally, configures the logging
        path and encoding to be used. If the logging path or encoding
        has changed, the file will be closed, reopened, and reattached
        to the logger.
        """

        if (
            not self._file_fh or
            self._file_fh.baseFilename != file_path or
            self._file_fh.encoding != file_encoding
        ):
            need_reattachment = False
            if self._file_fh:
                if self._file_fh in self.handlers:
                    need_reattachment = True
                self.removeHandler(self._file_fh)
                self._file_fh.close()

            self._file_fh = logging.FileHandler(
                file_path,
                encoding=file_encoding,
                delay=True,
            )

            if need_reattachment:
                self.addHandler(self._file_fh)

        self._stdout_flag = stdout_flag
        self._file_flag = file_flag

    def _log(self, *args, **kwargs):
        """
        If we are activated, passes log messages to super class. If not,
        buffers them to be passed after activation.
        """

        if self._activated:
            if self.handlers:
                super(BufferedLogger, self)._log(*args, **kwargs)

        else:
            self._buffer.append((args, kwargs))

    def activate(self, lookup):
        """
        Attach or detach handlers based on the lookup dict passed and
        the stdout_flag and file_flag that were passed to configure().
        If this is the first time being activated, any buffered log
        messages will be flushed out.
        """

        if self._stdout_flag and lookup[self._stdout_flag]:
            self.addHandler(self._stdout_sh)
        else:
            self.removeHandler(self._stdout_sh)

        if self._file_fh:
            if self._file_flag and lookup[self._file_flag]:
                self.addHandler(self._file_fh)
            else:
                self.removeHandler(self._file_fh)

        if not self._activated:
            self._activated = True

            while len(self._buffer):
                args, kwargs = self._buffer.pop(0)
                self._log(*args, **kwargs)  # use magic, pylint: disable=W0142

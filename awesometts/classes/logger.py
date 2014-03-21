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
import logging.handlers


def Logger(  # function masquerading as factory, pylint: disable=C0103
    name,
    handlers, formatter=None,
):
    """
    Returns a logger with the given name after configuring it. Any given
    name may be used only once; successive calls with the same name will
    raise an AssertionError.

    See the BufferedLogger configure() method for more information on
    the configuration options following the logger name.
    """

    default_cls = logging.getLoggerClass()

    logging.setLoggerClass(BufferedLogger)
    new_instance = logging.getLogger(name)
    logging.setLoggerClass(default_cls)

    new_instance.configure(  # will be a BufferedLogger, pylint: disable=E1103
        handlers,
        formatter,
    )
    return new_instance


class BufferedLogger(logging.Logger):  # lots inherited, pylint: disable=R0904
    """
    Extends the built-in logger to support buffered logs, i.e. logs that
    can be written to before handlers are setup. This is handy for when
    we don't know until later in program execution whether the user even
    wants logging to take place.
    """

    BUFFER_LIMIT = 10000

    __slots__ = [
        '_handlers',    # map of flags to possible handlers
        '_configured',  # True if configure() has been called
        '_activated',   # True if activate() has been called at least once
    ]

    def __init__(self, *args, **kwargs):
        """
        Note that because we do not call this directly and instead the
        logging module does the calling and only knows about names, some
        setup is deferred until the configure() method. If calling code
        uses the Logger factory function defined at the module level,
        both __init__ and configure() will be called automatically.
        """

        super(BufferedLogger, self).__init__(*args, **kwargs)

        self._handlers = None
        self._configured = False
        self._activated = False
        self.setLevel(logging.DEBUG)

    def configure(self, handlers, formatter=None):
        """
        Configures the flags that will trigger the logger to use various
        handlers. In the passed dict, each key should be a possible key
        to be passed to activate(), and each value should be a handler.
        """

        assert not self._configured, "Loggers may only be configured once"

        self._handlers = {
            flag: (logging.handlers.MemoryHandler(self.BUFFER_LIMIT), handler)
            for flag, handler
            in handlers.items()
        }
        self._configured = True

        for temp_handler, final_handler in self._handlers.values():
            if formatter:
                final_handler.setFormatter(formatter)
            self.addHandler(temp_handler)

    def activate(self, lookup):
        """
        Attach or detach handlers based on the lookup dict passed and
        the handlers that were registered with the configure() method.
        If this is the first time being activated, any buffered log
        messages will be flushed out.
        """

        assert self._configured, "Must configure Loggers before activation"

        if self._activated:
            for flag, handler in self._handlers.items():
                if lookup[flag]:
                    self.addHandler(handler)
                else:
                    self.removeHandler(handler)

        else:
            for flag, (temp_handler, final_handler) in self._handlers.items():
                if lookup[flag]:
                    temp_handler.setTarget(final_handler)
                    temp_handler.flush()

                self.removeHandler(temp_handler)
                if lookup[flag]:
                    self.addHandler(final_handler)

                self._handlers[flag] = final_handler

            self._activated = True

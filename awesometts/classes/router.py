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
Dispatch management of available services
"""

__all__ = ['Router']


class Router(object):
    """
    Allows the registration, lookup, and routing of services.
    """

    __slots__ = [
        '_cache_dir',
        '_conf',
        '_logger',
        '_lookup',
    ]

    def __init__(self, services, paths, conf, logger):
        """
        The services should be a list of tuples, where each tuple
        contains a unique service code and a class implementing the
        Service interface.

        The paths object should be a dict with the following keys:

            - cache (str): semi-persistent for services to store files
            - temp (str): temporary storage for scratch and transcoding

        The conf object should have a readable and settable dict-like
        interface with the following keys available:

            - lame_flags (str): parameters to pass to LAME transcoder
            - last_service (str): key to the last service used
            - last_options (dict): mapping of last options per service

        The logger object should have an interface like the one used by
        the standard library logging module, with debug(), info(), and
        so on, available.
        """

        self._cache_dir = paths['cache']
        self._conf = conf
        self._logger = logger
        self._lookup = {}

        for code, impl in services:
            name = None

            try:
                name = impl.NAME

                self._logger.info("Initializing %s service...", name)

                instance = impl(
                    temp_dir=paths['temp'],
                    lame_flags=conf['lame_flags'],
                    logger=logger,
                )

                self._lookup[code] = name, instance
                self._logger.info("%s service initialized", name)

            except:  # allow recovery from any exception, pylint:disable=W0702
                from traceback import format_exc

                self._logger.warn(
                    "Cannot initialize %s service; omitting\n%s",
                    name or code,
                    '\n'.join([
                        "!!! " + line
                        for line in format_exc().split('\n')
                    ]),
                )

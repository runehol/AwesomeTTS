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
        '_lookup',
    ]

    def __init__(self, services, conf, logger):

        self._lookup = {}

        for service_code, service_class in services:
            desc = None

            try:
                desc = service_class.desc()

                instance = service_class(
                    service_code,
                    conf,
                    logger,
                )

                options = instance.options()

                self._lookup[service_code] = instance, desc, options

            except service_class.UnavailableError:
                pass

            except:  # allow recovery from any exception, pylint:disable=W0702
                from sys import stderr
                from traceback import format_exc

                stderr.write(
                    "The AwesomeTTS %s service could not be initialized. If "
                    "this persists, note the error below and open an issue "
                    "at <https://github.com/AwesomeTTS/AwesomeTTS/issues>.\n"
                    "\n"
                    "%s\n"
                    "\n" % (
                        desc if desc else service_code,
                        format_exc(),
                    )
                )

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
    Allows the registration, lookup, and routing of concrete Service
    implementations.

    By having a routing-like object sit in-between the UI and the actual
    service code, Service implementations can be lazily loaded and their
    results can be cached, transparently to both sides.

    The router does NOT, however, handle threading issues, which remain
    in the domain of the UI. It should be expected that calls into the
    router may block, particularly those that require the initialization
    or running of Service code.
    """

    __slots__ = [
        '_aliases',    # dict mapping alternate service IDs
        '_conf',       # dict with lame_flags, last_service, last_options
        '_logger',     # logger-like interface with debug(), info(), etc.
        '_lookup',     # dict mapping service IDs to lookup information
        '_memoized',   # dict with various memoized items
        '_normalize',  # callable for sanitizing service IDs
        '_paths',      # dict with cache, temp
    ]

    def __init__(self, services, paths, conf, logger):
        """
        The services should be a dict with the following keys:

            - mappings (list of tuples): each with service ID, class
            - normalize (callable): for sanitizing service IDs

        The services may contain the following key:

            - aliases (list of tuples): alternate-to-official service IDs

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

        self._conf = conf
        self._logger = logger
        self._memoized = {}
        self._normalize = services['normalize']
        self._paths = paths

        self._aliases = {
            self._normalize(from_svc_id): self._normalize(to_svc_id)
            for from_svc_id, to_svc_id in services.get('aliases', [])
        }

        self._lookup = {
            self._normalize(svc_id): {
                'class': svc_class,
                'name': svc_class.NAME or svc_id,
                'traits': svc_class.TRAITS or [],
            }
            for svc_id, svc_class in services['mappings']
        }

    def get_services(self):
        """
        Returns the list of available services and the index of the last
        used service (last_service from the conf object) in that list.
        """

        for service in self._lookup.values():
            self._load_service(service)

        if not 'services_items' in self._memoized:
            self._logger.debug("Building the services list")
            self._memoized['services_items'] = {
                'items': sorted([
                    (svc_id, service['name'])
                    for svc_id, service in self._lookup.items()
                    if service['instance']
                ], key=lambda (svc_id, text): text.lower()),

                'index': 0,
            }

        services = self._memoized['services_items']

        try:
            last_service = self._normalize(self._conf['last_service'])
            if last_service in self._aliases:
                last_service = self._aliases[last_service]

            services['index'] = services['items'].index(next(
                item
                for item in services['items']
                if item[0] == last_service
            ))

        except StopIteration:
            pass

        return services

    def get_desc(self, svc_id):
        """
        Returns the description associated with the service.
        """

        svc_id, service = self._fetch_service(svc_id)

        if 'desc' not in service:
            self._logger.debug(
                "Retrieving the description for %s",
                service['name'],
            )
            service['desc'] = service['instance'].desc()

        return service['desc']

    def get_options(self, svc_id):
        """
        Returns a list of options that should be displayed for the
        service, with defaults highlighted and the indices of the last
        used option items (from last_options in the conf object) or the
        default option items.
        """

        svc_id, service = self._fetch_service(svc_id)

        if 'options' not in service:
            self._logger.debug(
                "Building the options list for %s",
                service['name'],
            )
            service['options'] = [
                dict(
                    option.items() +
                    [
                        (
                            'items',
                            option['items'] if 'default' not in option
                            else [
                                item if item[0] != option['default']
                                else (item[0], item[1] + " [default]")
                                for item in option['items']
                            ]
                        ),
                        ('index', '0'),
                        ('key', self._normalize(option['key'])),
                    ]
                )
                for option in service['instance'].options()
            ]

        options = service['options']

        last_options = self._conf['last_options'].get(svc_id, {})

        for option in options:
            try:
                last_option = last_options[option['key']]
                option['index'] = option['items'].index(next(
                    item
                    for item in option['items']
                    if item[0] == last_option
                ))

            except (KeyError, StopIteration):
                if 'default' in option:
                    default_option = option['default']
                    option['index'] = option['items'].index(next(
                        item
                        for item in option['items']
                        if item[0] == default_option
                    ))

        return options

    def _fetch_service(self, svc_id):
        """
        Finds the service using the svc_id, normalizing it and using the
        aliases list, initializes it this is its first use, and returns
        the normalized svc_id and service lookup dict.

        Raises KeyError if a bad svc_id is passed.

        Raises EnvironmentError if a good svc_id is passed, but the
        given service is not available for this session.
        """

        svc_id = self._normalize(svc_id)
        if svc_id in self._aliases:
            svc_id = self._aliases[svc_id]

        try:
            service = self._lookup[svc_id]
        except KeyError:
            raise KeyError("There is no '%s' service" % svc_id)

        self._load_service(service)

        if not service['instance']:
            raise EnvironmentError(
                "The %s service is not currently available" %
                service['name']
            )

        return svc_id, service

    def _load_service(self, service):
        """
        Given a service lookup dict, tries to initialize the service if
        it is not already initialized. Exceptions are trapped and logged
        with the 'instance' then set to None. Successful initializations
        set the 'instance' to the resulting object.
        """

        if 'instance' in service:
            return

        self._logger.info("Initializing %s service...", service['name'])

        try:
            service['instance'] = service['class'](
                temp_dir=self._paths['temp'],
                lame_flags=self._conf['lame_flags'],
                logger=self._logger,
            )

            self._logger.info("%s service initialized", service['name'])

        except:  # allow recovery from any exception, pylint:disable=W0702
            service['instance'] = None  # flag this service as unavailable

            from traceback import format_exc
            trace_lines = format_exc().split('\n')

            self._logger.warn(
                "Initialization failed for %s service\n%s",
                service['name'],
                '\n'.join(["!!! " + line for line in trace_lines]),
            )

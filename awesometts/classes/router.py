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

from . import Bundle
from .services import Trait as BaseTrait


class Router(object):
    """
    Allows the registration, lookup, and routing of concrete Service
    implementations.

    By having a routing-like object sit in-between the UI and the actual
    service code, Service implementations can be lazily loaded and their
    results can be cached, transparently to both sides.

    Additionally, some methods on the router offer callbacks. In this
    case, if the method is going to call a service that might block,
    then the method can arrange for that call to occur on a different
    thread and then call the callback when done. Otherwise, the callback
    can be called immediately with neither blocking nor threading.
    """

    Trait = BaseTrait

    __slots__ = [
        '_config',     # dict with lame_flags, last_service, last_options
        '_logger',     # logger-like interface with debug(), info(), etc.
        '_normalize',  # callable for sanitizing service IDs
        '_paths',      # bundle with cache, temp
        '_services',   # bundle with aliases, avail, lookup
        '_textize',    # callable for sanitizing input text
    ]

    def __init__(self, services, paths, config, logger):
        """
        The services should be a bundle with the following:

            - mappings (list of tuples): each with service ID, class
            - aliases (list of tuples): alternate-to-official service IDs
            - normalize (callable): for sanitizing service IDs
            - textize (callable): for sanitizing human input text

        The paths object should be a bundle with the following:

            - cache (str): semi-persistent for services to store files
            - temp (str): temporary storage for scratch and transcoding

        The config object should have a readable and settable dict-like
        interface with the following keys available:

            - lame_flags (str): parameters to pass to LAME transcoder
            - last_service (str): key to the last service used
            - last_options (dict): mapping of last options per service

        The logger object should have an interface like the one used by
        the standard library logging module, with debug(), info(), and
        so on, available.
        """

        self._config = config
        self._logger = logger
        self._normalize = services.normalize
        self._paths = paths
        self._textize = services.textize

        self._services = Bundle()

        self._services.aliases = {
            self._normalize(from_svc_id): self._normalize(to_svc_id)
            for from_svc_id, to_svc_id in services.aliases
        }

        self._services.avail = None

        self._services.lookup = {
            self._normalize(svc_id): {
                'class': svc_class,
                'name': svc_class.NAME or svc_id,
                'traits': svc_class.TRAITS or [],
            }
            for svc_id, svc_class in services.mappings
        }

    def by_trait(self, trait):
        """
        Returns a list of service names that advertise the given trait.
        """

        return [
            service['name']
            for service
            in self._services.lookup.values()
            if trait in service['traits']
        ]

    def get_services(self):
        """
        Returns the list of available services and the index of the last
        used service (last_service from the config object) in that list.
        """

        if not self._services.avail:
            self._logger.debug("Building the list of services...")

            for service in self._services.lookup.values():
                self._load_service(service)

            self._services.avail = {
                'items': sorted([
                    (svc_id, service['name'])
                    for svc_id, service in self._services.lookup.items()
                    if service['instance']
                ], key=lambda (svc_id, text): text.lower()),
            }

            self._services.avail.update({
                'index': 0,
                'value': self._services.avail['items'][0][0],
            })

        services = self._services.avail

        last_service = self._normalize(self._config['last_service'])
        if last_service in self._services.aliases:
            last_service = self._services.aliases[last_service]

        if last_service != services['value']:
            try:
                self._logger.debug("Setting last service: %s", last_service)

                services['index'] = services['items'].index(next(
                    item
                    for item in services['items']
                    if item[0] == last_service
                ))
                services['value'] = last_service

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
        used option items (from last_options in the config object) or
        the default option items.
        """

        svc_id, service, options = self._fetch_options(svc_id)
        last_options = self._config['last_options'].get(svc_id, {})

        for option in options:
            try:
                last_option = last_options[option['key']]

                if last_option != option['value']:
                    self._logger.debug(
                        "Setting %s service's %s (%s) to the last used: %s",
                        service['name'],
                        option['key'],
                        option['label'],
                        last_option,
                    )

                    option['index'] = option['items'].index(next(
                        item
                        for item in option['items']
                        if item[0] == last_option
                    ))
                    option['value'] = last_option

            except (KeyError, StopIteration):
                if 'default' in option:
                    default_option = option['default']

                    if default_option != option['value']:
                        self._logger.debug(
                            "Setting %s service's %s (%s) to the default: %s",
                            service['name'],
                            option['key'],
                            option['label'],
                            default_option,
                        )

                        option['index'] = option['items'].index(next(
                            item
                            for item in option['items']
                            if item[0] == default_option
                        ))
                        option['value'] = default_option

        return options

    def play(self, svc_id, text, options, callback=None):
        """
        Playback the text with the given options on the service
        identified by svc_id. All input is normalized before processing
        it, resulting in a consistent hashed filename. Options are
        validated against what the service reports being available.

        Cache hits are played back via Anki's API and a callback made to
        the callback, if specified, immediately. Otherwise, the service
        run() method is called before playback and the callback occur.
        """

        self._logger.debug(
            "Received play request to '%s' with %s\n%s",
            svc_id,
            options,
            "\n".join(["<<< " + line for line in text.split("\n")])
        )

        svc_id, service, svc_options = self._fetch_options(svc_id)
        svc_options_keys = [svc_option['key'] for svc_option in svc_options]
        text = self._textize(text)
        options = {
            key: value
            for key, value in [
                (self._normalize(key), value)
                for key, value in options.items()
            ]
            if key in svc_options_keys
        }

        incorrect_svc_options = []
        missing_svc_options = []

        for svc_option in svc_options:
            key = svc_option['key']
            if key in options:
                try:
                    normalized_value = (
                        options[key] if 'normalize' not in svc_option
                        else svc_option['normalize'](options[key])
                    )

                    if 'validate' in svc_option:
                        if not svc_option['validate'](normalized_value):
                            raise ValueError

                    else:
                        next(
                            True
                            for item in svc_option['items']
                            if item[0] == normalized_value
                        )

                    options[key] = normalized_value

                except (StopIteration, ValueError):
                    incorrect_svc_options.append(svc_option)

            elif 'default' in svc_option:
                options[key] = svc_option['default']

            else:
                missing_svc_options.append(svc_option)

        if incorrect_svc_options or missing_svc_options:
            problems = []

            if incorrect_svc_options:
                problems.append(
                    "incorrect parameters be fixed (%s)" % ", ".join([
                        "'%s' for the %s cannot be set to '%s'" % (
                            svc_option['key'],
                            svc_option['label'],
                            options[svc_option['key']],
                        )
                        for svc_option in incorrect_svc_options
                    ])
                )

            if missing_svc_options:
                problems.append(
                    "required parameters be supplied (%s)" % ", ".join([
                        "'%s' for the %s" % (
                            svc_option['key'],
                            svc_option['label'],
                        )
                        for svc_option in missing_svc_options
                    ])
                )

            raise ValueError(
                "Playback with the '%s' (%s) service requires that %s" %
                (svc_id, service['name'], " and ".join(problems))
            )

        path = self._path_cache(svc_id, text, options)

        from os.path import exists
        cache_hit = exists(path)

        self._logger.debug(
            "Interpreted as request to '%s' w/ %s and \"%s\" using %s (%s)",
            svc_id,
            options,
            text,
            path,
            "cache hit" if cache_hit else "need to record asset"
        )

        if cache_hit:
            from anki.sound import play
            play(path)

            if callback:
                callback()

            return

        # FIXME the following needs to be re-written to support threads

        try:
            service['instance'].run(text, options, path)

            from anki.sound import play
            play(path)

        except Exception as exception:  # capture all, pylint:disable=W0703
            if callback:
                callback(exception)
            else:
                raise

            return

        if callback:
            callback()

    def _fetch_options(self, svc_id):
        """
        Identifies the service by its ID, checks to see if the options
        list need construction, and then return back the normalized ID,
        service lookup dict, and options list.
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
                        ('value', option['items'][0][0]),
                        ('key', self._normalize(option['key'])),
                    ]
                )
                for option in service['instance'].options()
            ]

        return svc_id, service, service['options']

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
        if svc_id in self._services.aliases:
            svc_id = self._services.aliases[svc_id]

        try:
            service = self._services.lookup[svc_id]
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
                temp_dir=self._paths.temp,
                lame_flags=self._config['lame_flags'],
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

    def _path_cache(self, svc_id, text, options):
        """
        Returns a consistent cache path given the svc_id, text, and
        options. This can be used to repeat the same request yet reuse
        the same path.
        """

        hash_input = '/'.join([
            text,
            svc_id,
            ';'.join(
                '='.join([key, str(value)])
                for key, value
                in sorted(options.items())
            )
        ])

        from hashlib import sha1
        from os.path import join

        return join(
            self._paths.cache,
            '.'.join([
                '-'.join([
                    svc_id,
                    sha1(
                        hash_input.encode('utf-8')
                        if isinstance(hash_input, unicode)
                        else hash_input
                    ).hexdigest(),
                ]),
                'mp3',
            ]),
        )

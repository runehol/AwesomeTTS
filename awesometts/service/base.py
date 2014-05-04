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
Base class for service implementations

Provides an abstract Service class that can be extended for implementing
TTS services for use with AwesomeTTS.
"""

__all__ = ['Service']

import abc
import sys
import subprocess


class Service(object):
    """
    Represents a TTS service, providing an interface for the framework
    to interact with the service (initialization, description, options,
    and running) in addition to helpers that concrete implementations
    can call into to fulfill the interface (e.g. CLI calls, downloading
    files from the Internet).

    Although not enforced by Python's abc module, concrete classes
    should also specify NAME and TRAITS constants, which the framework
    can use before initializing a service.

    Methods that concrete classes must implement will only be called
    when they are needed (i.e. they are lazily loaded). In addition,
    with the exception of the run() method, these methods will only be
    called once during a particular session (i.e. their results will be
    cached). The run() method will usually only be called one time for a
    particular set of arguments (because the media files it produces are
    retained on the file system).
    """

    __metaclass__ = abc.ABCMeta

    __slots__ = [
        '_lame_flags',  # for passing to LAME transcoder
        '_logger',      # logging interface with debug(), info(), etc.
        'normalize',    # callable for standardizing string values
        '_temp_dir',    # for temporary scratch space
    ]

    # where we can find the lame transcoder
    CLI_LAME = 'lame'

    # startup information for Windows to keep command window hidden
    CLI_SI = None

    # will be set to True if user is running Linux
    IS_LINUX = False

    # will be set to True if user is running Mac OS X
    IS_MACOSX = False

    # will be set to True if user is running Windows
    IS_WINDOWS = False

    # abstract; to be overridden by the concrete classes
    # e.g. NAME = "ABC Service API"
    NAME = None

    # abstract; to be overridden by the concrete classes
    # e.g. TRAITS = [Trait.INTERNET, Trait.TRANSCODING]
    TRAITS = None

    def __init__(self, temp_dir, lame_flags, normalize, logger):
        """
        Attempt to initialize the service, raising a exception if the
        service cannot be used. If the service needs to make any calls
        to determine its viability (e.g. check to see if voices are
        installed on the system), they should be made here.

        This method will be called the first time the user displays the
        list of services or the first time the framework encounters an
        on-the-fly TTS tag for the service.

        The temp_dir will be used as the base for paths that are needed
        only temporarily (e.g. temporary input files to feed services,
        temporary audio files that need to be transcoded to MP3).

        The lame_flags will be passed to LAME transcoder if the service
        needs to transcode between different audio file types.

        The logger object should have an interface like the one used by
        the standard library logging module, with debug(), info(), and
        so on, available.
        """

        assert self.NAME, "Please specify a NAME for the service"
        assert self.TRAITS, "Please specify a TRAITS list for the service"

        self._lame_flags = lame_flags
        self._logger = logger
        self.normalize = normalize
        self._temp_dir = temp_dir

    @abc.abstractmethod
    def desc(self):
        """
        Return a human-readable description of this service.

        This method will be called the first time the user displays the
        service (e.g. as part of a panel).
        """

        return ""

    @abc.abstractmethod
    def options(self):
        """
        Return a list of settable options for this service, in the order
        that they should be presented to the user.

        This method will be called the first time the user displays the
        service (e.g. as part of a panel), or the first time a set of
        options must be built to call the service (e.g. encountering an
        on-the-fly TTS tag for the service).

        The list should follow a structure like this:

            return [
                dict(
                    key='voice',
                    label="Voice",
                    values=[
                        ('en-us', "American English"),
                        ('en-es', "American Spanish"),
                    ],
                    transform=lambda value: ''.join(
                        char
                        for char in value.strip().lower()
                        if char.isalpha() or char == '-'
                    ),
                ),

                dict(
                    key='speed',
                    label="Speed",
                    items=(150, 175, "wpm"),
                    transform=int,
                    default=175,
                ),
            ]

        Each dict must include 'key', 'label', and 'items'. A dict may
        include 'default', if there is one. An option without a given
        'default' will be considered to be required (e.g. when parsing
        on-the-fly TTS tags for the service).

        If specified, 'normalize' will be used to clean up user input
        before processing it.
        """

        return {}

    @abc.abstractmethod
    def run(self, text, options, path):
        """
        Run the service and generate a file at the given path using the
        text and selected options. The passed options will correspond
        with those returned by the options() method.

        A sample call might look like this:

            service.run(
                text="Hello world.",
                options={'voice': 'en-us', 'speed': 200},
                path='/home/user/Anki/addons/awesometts/cache/file.mp3',
            )

        All processing done within this function is allowed to block, as
        the caller is to have already taken care of threading if it is
        necessary to prevent locking of the UI.

        Additionally, it is expected that the caller has already checked
        to see if a temporary file already exists at the given path. If
        it does, the caller will use that file directly rather than
        calling into the run() method.

        If output cannot be written to the path, an exception should be
        raised so the caller knows why.
        """

    def cli_call(self, *args):
        """
        Executes a command line call for its side effects. May be passed
        as a single list or as multiple arguments.
        """

        self._cli_exec(
            subprocess.check_call,
            args,
            "for processing",
        )

    def cli_output(self, *args):
        """
        Executes a command line call to examine its output, returned as
        a list of lines. May be passed as a single list or as multiple
        arguments.
        """

        returned = self._cli_exec(
            subprocess.check_output,
            args,
            "to inspect output",
        )

        if not returned:
            raise EnvironmentError("Call returned no output")

        returned = returned.strip()

        if not returned:
            raise EnvironmentError("Call returned whitespace")

        returned = returned.split('\n')

        self._logger.debug(
            "Received %d %s of output from call\n%s",
            len(returned),
            "lines" if len(returned) != 1 else "line",
            '\n'.join(["<<< " + line for line in returned]),
        )

        return returned

    def cli_transcode(self, input_path, output_path):
        """
        Runs the LAME transcoder to create a new MP3 file.
        """

        self.cli_call(
            self.CLI_LAME,
            self._lame_flags.split(),
            input_path,
            output_path,
        )

    def _cli_exec(self, callee, args, purpose):
        """
        Handles the underlying system call, logging, and exceptions when
        a call to cli_call() or cli_output() is made.
        """

        args = [
            arg if isinstance(arg, basestring) else str(arg)
            for arg in self._flatten(args)
        ]

        self._logger.debug(
            "Calling %s binary with %s %s",
            args[0],
            args[1:] if len(args) > 1 else "no arguments",
            purpose,
        )

        return callee(args, startupinfo=self.CLI_SI)

    def net_download(self, path, addr, query=None, require=None):
        """
        Downloads a file to the given from the specified address and
        optional query string. Additionally, a require dict may be
        passed to enforce a status code (key 'status') and/or
        Content-Type (key 'mime').
        """

        # TODO Test this code against a system proxy. Previously, this
        # needed to be prepended by hand for mplayer's sake, but we are
        # no longer passing URLs directly to mplayer. The documentation
        # for urllib2 leads me to believe that it might be handled
        # automatically. The old code worked as follows...
        #
        # PROXIES = urllib.getproxies()
        # if PROXIES and 'http' in PROXIES:
        #     URL = '/'.join([
        #         PROXIES['http'].replace('http:', 'http_proxy:').rstrip('/'),
        #         URL,
        #     ])

        # TODO Ensure that the caller of run(), which will call this, is
        # capable of catching and gracefully handling exceptions thrown
        # here so as to not annoy the user.

        from urllib2 import urlopen, Request, quote

        url = addr if not query else '?'.join([
            addr,
            '&'.join([
                '='.join([
                    key,
                    quote(
                        value.encode('utf-8') if isinstance(value, unicode)
                        else value,
                        safe='',
                    ),
                ])
                for key, value in query.items()
            ])
        ])

        self._logger.debug("Fetching %s from the web", url)

        response = urlopen(
            Request(url=url, headers={'User-Agent': 'Mozilla/5.0'}),
            timeout=15,
        )

        if not response:
            raise IOError("No response from web request")

        if require:
            if (
                'status' in require and
                require['status'] != response.getcode()
            ):
                raise ValueError(
                    "Web request returned %d status code; wanted %d" % (
                        response.getcode(),
                        require['status'],
                    )
                )

            if (
                'mime' in require and
                require['mime'] != response.info().gettype()
            ):
                raise ValueError(
                    "Web request returned %s Content-Type; wanted %s" % (
                        response.info().gettype(),
                        require['mime'],
                    )
                )

        with open(path, 'wb') as response_output:
            response_output.write(response.read())

        response.close()

    def path_temp(self, extension):
        """
        Returns a path using the given extension that may be used for
        writing out a temporary file.
        """

        from string import ascii_lowercase, digits
        alphanumerics = ascii_lowercase + digits

        from os.path import join
        from random import choice
        from time import time
        return join(
            self._temp_dir,
            '%x-%s.%s' % (
                int(time()),
                ''.join(choice(alphanumerics) for i in range(30)),
                extension,
            ),
        )

    def path_unlink(self, *args):
        """
        Attempts to remove the given file(s), ignoring any failures. May
        be passed as a single list or as multiple arguments.
        """

        from os import unlink
        for path in self._flatten(args):
            if path:
                try:
                    unlink(path)
                    self._logger.debug("Deleted %s from file system", path)

                except OSError:
                    self._logger.warn("Unable to delete %s", path)

    def path_workaround(self, text):
        """
        If running on Windows and the given text cannot be represented
        purely with ASCII characters, returns a path to a temporary
        text file that may be used to feed a service binary.

        Returns False otherwise.
        """

        if self.IS_WINDOWS:
            try:
                text.encode('ascii')

            except UnicodeError:
                temporary_txt = self.path_temp('txt')

                from codecs import open as copen
                with copen(temporary_txt, mode='w', encoding='utf-8') as out:
                    out.write(text)

                return temporary_txt

        return False

    def reg_hklm(self, key, name):
        """
        Attempts to retrieve a value within the local machine tree
        stored at the given key and value name.
        """

        self._logger.debug(
            "Reading %s at %s from the Windows registry",
            name,
            key,
        )

        import _winreg as wr  # for Windows only, pylint: disable=F0401
        with wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE) as hklm:
            with wr.OpenKey(hklm, key) as subkey:
                return wr.QueryValueEx(subkey, name)[0]

    @classmethod
    def _flatten(cls, iterable):
        """
        Given a potentially nested iterable, returns a flat iterable.
        """

        for item in iterable:
            if isinstance(item, list) or isinstance(item, tuple):
                for subitem in cls._flatten(item):
                    yield subitem

            else:
                yield item


# Reinitialize the CLI_LAME, CLI_SI, IS_WINDOWS, and IS_MACOSX constants
# on the base class, if necessary given the running operating system.

if subprocess.mswindows:
    Service.CLI_LAME = 'lame.exe'
    Service.CLI_SI = subprocess.STARTUPINFO()
    Service.IS_WINDOWS = True

    try:
        Service.CLI_SI.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    except AttributeError:
        try:
            Service.CLI_SI.dwFlags |= (
                subprocess._subprocess.  # workaround, pylint:disable=W0212
                STARTF_USESHOWWINDOW
            )

        except AttributeError:
            pass

elif sys.platform.startswith('darwin'):
    Service.IS_MACOSX = True

elif sys.platform.startswith('linux'):
    Service.IS_LINUX = True

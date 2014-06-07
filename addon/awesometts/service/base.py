# -*- coding: utf-8 -*-
# pylint:disable=bad-continuation

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
import os
import shutil
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
        '_lame_flags',  # callable to get flag string for LAME transcoder
        '_logger',      # logging interface with debug(), info(), etc.
        'normalize',    # callable for standardizing string values
        '_temp_dir',    # for temporary scratch space
    ]

    # when getting CLI output, try using these decodings, in this order
    CLI_DECODINGS = ['ascii', 'utf-8', 'latin-1']

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

        The lame_flags is a callable to retrieve a string of flags to be
        passed to LAME transcoder if the service needs to transcode
        between different audio file types.

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

        if not isinstance(returned, unicode):
            for encoding in self.CLI_DECODINGS:
                try:
                    returned = returned.decode(encoding)
                    self._logger.info("CLI decoding success w/ %s", encoding)
                    break
                except (LookupError, UnicodeError):
                    self._logger.warn("CLI decoding failed w/ %s", encoding)
                    pass
            else:
                self._logger.error("All CLI decodings failed; forcing ASCII")
                returned = returned.decode('ascii', errors='ignore')

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

    def cli_transcode(self, input_path, output_path, require=None):
        """
        Runs the LAME transcoder to create a new MP3 file.

        Note that instead of writing the file immediately to the given
        output path, this method first writes it a temporary file and
        then moves it to the output path afterward. This works around a
        bug on Windows where a user with a non-ASCII username would have
        a non-ASCII output_path, causing an error when the path is sent
        via the CLI. However, because the temporary directory on Windows
        will be of the all-ASCII variety, we can send it through there
        first and then move it to its final home.
        """

        if not os.path.exists(input_path):
            raise RuntimeError(
                "The input file to transcode to an MP3 could not be found. "
                "Please report this problem if it persists."
            )

        if (
            require and 'size_in' in require and
            os.path.getsize(input_path) < require['size_in']
        ):
            raise ValueError(
                "Input to transcoder was %d-byte stream; wanted %d+ bytes "
                "(the service might not have liked your input text)" % (
                    os.path.getsize(input_path),
                    require['size_in'],
                )
            )

        intermediate_path = self.path_temp('mp3')  # see note above

        try:
            self.cli_call(
                self.CLI_LAME,
                self._lame_flags().split(),
                input_path,
                intermediate_path,
            )

        except OSError as os_error:
            from errno import ENOENT
            if os_error.errno == ENOENT:
                raise OSError(
                    ENOENT,
                    "Unable to find lame to transcode the audio. "
                    "It might not have been installed.",
                )
            else:
                raise

        if not os.path.exists(intermediate_path):
            raise RuntimeError(
                "Transcoding the audio stream failed. Are the flags you "
                "specified for LAME (%s) okay?" % self._lame_flags()
            )

        shutil.move(intermediate_path, output_path)  # see note above

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

        The underlying library here already understands how to search
        the environment for proxy settings (e.g. HTTP_PROXY), so we do
        not need to do anything extra for that.
        """

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

        payload = response.read()
        response.close()

        if require and 'size' in require and len(payload) < require['size']:
            raise ValueError(
                "Web request returned a %d-byte stream; wanted %d+ bytes" % (
                    len(payload),
                    require['size'],
                )
            )

        with open(path, 'wb') as response_output:
            response_output.write(payload)

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
                return self.path_input(text)

        return False

    def path_input(self, text):
        """
        Returns a path to a file containing the given unicode text.
        """

        temporary_txt = self.path_temp('txt')

        from codecs import open as copen
        with copen(temporary_txt, mode='w', encoding='utf-8') as out:
            out.write(text)

        return temporary_txt

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
    Service.CLI_DECODINGS.append('mbcs')
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

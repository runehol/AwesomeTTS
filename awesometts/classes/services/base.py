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
Base classes for service implementations
"""

__all__ = ['Service']

import abc
import subprocess


class Service(object):
    """
    Interface for interacting with a service. All services must be able
    to be initialized, return a description, return their available
    options, and output text to a file.
    """

    __metaclass__ = abc.ABCMeta

    __slots__ = [
        '_code',        # unique identifier for this service
        '_lame_flags',  # for passing to LAME transcoder
        '_logger',      # logging interface with debug(), info(), etc.
        '_temp_dir',    # for temporary scratch space
    ]

    # startup information for Windows to keep command window hidden
    CLI_SI = None

    # will be set to True if user is running Windows
    WINDOWS = False

    @classmethod
    @abc.abstractmethod
    def desc(cls):
        """
        Return a human-readable description of this service.
        """

        return ""

    def __init__(self, code, temp_dir, lame_flags, logger):
        """
        Attempt to initialize the service, raising any exception if the
        service cannot be used.

        The code identifies the service uniquely across all the other
        services, and may be used in filenames and other places.

        The temp_dir will be used as the base for paths that are needed
        only temporarily (e.g. temporary input files to feed services,
        temporary audio files that need to be transcoded to MP3).

        The lame_flags will be passed to LAME transcoder if the service
        needs to transcode between different audio file types.

        The logger object should have an interface like the one used by
        the standard library logging module, with debug(), info(), and
        so on, available.
        """

        self._code = code
        self._lame_flags = lame_flags
        self._logger = logger
        self._temp_dir = temp_dir

    @abc.abstractmethod
    def options(self):
        """
        Return a list of settable options for this service, in the order
        that they should be presented to the user.

        The list should follow a structure like this:

            return [
                dict(
                    key='voice',
                    label="Voice",
                    options=[
                        ('en-us', "American English"),
                        ('en-es', "American Spanish"),
                    ],
                ),

                dict(
                    key='speed',
                    label="Speed",
                    options=[
                        (150, '150 wpm'),
                        (175, '175 wpm'),
                        (200, '200 wpm'),
                    ],
                    default=175,
                ),
            ]
        """

        return {}

    @abc.abstractmethod
    def run(self, text, options, path):
        """
        Run the service and generate a file at the given path using the
        text and selected options. The passed options will correspond
        with those returned by the options() method.

        A sample call might look like this:

            service.play(
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

    def cli_call(self, binary, *args):
        """
        Execute a command line call for its side effects.
        """

        self._cli_exec(
            subprocess.check_call,
            binary,
            args,
            "for processing",
        )

    def cli_output(self, binary, *args):
        """
        Execute a command line call to examine its output, returned as
        a list of lines.
        """

        returned = self._cli_exec(
            subprocess.check_output,
            binary,
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

    def _cli_exec(self, callee, binary, args, purpose):
        """
        Handle the underlying system call, logging, and exceptions.
        """

        self._logger.debug(
            "Calling %s binary with %s %s",
            binary,
            args if args else "no arguments",
            purpose,
        )

        return callee([binary] + list(args), startupinfo=self.CLI_SI)

    def reg_hklm(self, key, name):
        """
        Attempt to retrieve a value within the local machine tree stored
        at the given key and value name.
        """

        import _winreg as wr  # for Windows only, pylint: disable=F0401

        self._logger.debug(
            "Reading %s at %s from the Windows registry",
            name,
            key,
        )

        with wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE) as hklm:
            with wr.OpenKey(hklm, key) as subkey:
                return wr.QueryValueEx(subkey, name)[0]


if subprocess.mswindows:
    Service.CLI_SI = subprocess.STARTUPINFO()
    Service.WINDOWS = True

    try:
        Service.CLI_SI.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except AttributeError:  # workaround for some Python implementations
        Service.CLI_SI.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW

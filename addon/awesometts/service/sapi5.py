# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
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
Service implementation for SAPI 5 on the Windows platform

This module functions with the help of a JScript gateway script. See
also the sapi5.js file in this directory.
"""

__all__ = 'SAPI5'

import os
import os.path

from .base import Service
from .common import Trait


class SAPI5(Service):
    """
    Provides a Service-compliant implementation for SAPI 5.
    """

    __slots__ = [
        '_binary',        # path to the cscript binary
        '_voice_list',    # list of installed voices as a list of tuples
    ]

    NAME = "Microsoft Speech API"

    TRAITS = [Trait.TRANSCODING]

    _SCRIPT = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'sapi5.js',
    )

    def __init__(self, *args, **kwargs):
        """
        Attempts to locate the cscript binary and read the list of
        voices from the `cscript.exe sapi5.js voice-list` output.

        However, if not running on Windows, no environment inspection is
        attempted and an exception is immediately raised.
        """

        if not self.IS_WINDOWS:
            raise EnvironmentError("SAPI 5 is only available on Windows")

        super(SAPI5, self).__init__(*args, **kwargs)

        self._binary = next(
            fullpath
            for windows in [
                os.environ.get('SYSTEMROOT', None),
                r'C:\Windows',
                r'C:\WinNT',
            ]
            if windows and os.path.exists(windows)
            for subdirectory in ['syswow64', 'system32', 'system']
            for filename in ['cscript.exe']
            for fullpath in [os.path.join(windows, subdirectory, filename)]
            if os.path.exists(fullpath)
        )

        output = [
            line.strip()
            for line in self.cli_output(
                self._binary,
                self._SCRIPT,
                'voice-list',
            )
        ]

        self._voice_list = sorted({
            (voice.strip(), voice.strip())
            for voice in output[output.index('__AWESOMETTS_VOICE_LIST__') + 1:]
            if voice.strip()
        }, key=lambda voice: voice[1].lower())

        if not self._voice_list:
            raise EnvironmentError("No voices in `sapi5.js voice-list`")

    def desc(self):
        """
        Returns a short, static description.
        """

        count = len(self._voice_list)
        return ("SAPI 5.0 via JScript (%d %s)" %
                (count, "voice" if count == 1 else "voices"))

    def options(self):
        """
        Provides access to voice, speed, and volume.
        """

        voice_lookup = {
            self.normalize(voice[0]): voice[0]
            for voice in self._voice_list
        }

        def transform_voice(value):
            """Normalize and attempt to convert to official voice."""

            normalized = self.normalize(value)

            return (
                voice_lookup[normalized] if normalized in voice_lookup
                else value
            )

        return [
            # See also sapi5.js when adjusting any of these

            dict(
                key='voice',
                label="Voice",
                values=self._voice_list,
                transform=transform_voice,
            ),

            dict(
                key='speed',
                label="Speed",
                values=(-10, 10),
                transform=int,
                default=0,
            ),

            dict(
                key='volume',
                label="Volume",
                values=(1, 100, "%"),
                transform=int,
                default=100,
            ),
        ]

    def run(self, text, options, path):
        """
        Converts input voice and text into hex strings, writes a
        temporary wave file, and then transcodes to MP3.
        """

        hexstr = lambda value: ''.join(['%04X' % ord(char) for char in value])

        output_wav = self.path_temp('wav')

        try:
            self.cli_call(
                self._binary,
                self._SCRIPT,
                'speech-output',
                output_wav,
                options['speed'],
                options['volume'],
                hexstr(options['voice']),
                hexstr(text),  # double dash unnecessary due to hex encoding
            )

            self.cli_transcode(
                output_wav,
                path,
                require=dict(
                    size_in=4096,
                ),
            )

        finally:
            self.path_unlink(output_wav)

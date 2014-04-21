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

This module functions with the help of a Visual Basic script. See also
the sapi5.vbs file in this directory.
"""

__all__ = 'SAPI5'

import os
import os.path
from .base import Service, Trait


class SAPI5(Service):
    """
    Provides a Service-compliant implementation for SAPI 5.
    """

    __slots__ = [
        '_binary',  # path to the cscript binary
        '_voices',  # list of installed voices as a list of tuples
    ]

    _SCRIPT = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'sapi5.vbs',
    )

    @classmethod
    def desc(cls):
        return "Microsoft Speech API (SAPI) 5"

    @classmethod
    def traits(cls):
        return [Trait.TRANSCODING]

    def __init__(self, *args, **kwargs):
        """
        Attempt to locate the cscript binary and read the list of voices
        from the `cscript.exe sapi5.vbs -vl` output.

        However, if not running on Windows, no environment inspection is
        attempted and an exception is immediately raised.
        """

        if not self.WINDOWS:
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

        output = self.cli_output(self._binary, self._SCRIPT, '-vl')

        self._voices = sorted({
            (voice.strip(), voice.strip())
            for voice in output[output.index('--Voice List--') + 1:]
            if voice.strip()
        }, key=lambda voice: voice[1].lower())

        if not self._voices:
            raise EnvironmentError("No usable output from `sapi5.vbs -vl`")

    def options(self):
        """
        Provides access to voice only.
        """

        return [
            dict(
                key='voice',
                label="Voice",
                options=self._voices,
            ),
        ]

    def run(self, text, options, path):
        """
        Convert input into hex strings, write a temporary wave file, and
        then transcode to MP3.
        """

        hexstr = lambda value: ''.join(['%04X' % ord(char) for char in value])

        output_wav = self.path_temp('wav')

        self.cli_call(
            self._binary, self._SCRIPT, '-hex',
            '-voice', hexstr(options['voice']),
            '-o', output_wav,
            hexstr(text),  # n.b. double dash is unnecessary due to hex string
        )

        self.cli_transcode(output_wav, path)

        self.path_unlink(output_wav)

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
"""

__all__ = 'SAPI5'

from .base import Service
from .common import Trait


class SAPI5(Service):
    """
    Provides a Service-compliant implementation for SAPI 5.
    """

    __slots__ = [
        '_client',     # reference to the win32com.client module
        '_pythoncom',  # reference to the pythoncom module
        '_voice_map',  # dict of voice names to their SAPI objects
    ]

    NAME = "Microsoft Speech API"

    TRAITS = [Trait.TRANSCODING]

    def __init__(self, *args, **kwargs):
        """
        Attempts to retrieve list of voices from the SAPI.SpVoice API.

        However, if not running on Windows, no environment inspection is
        attempted and an exception is immediately raised.
        """

        if not self.IS_WINDOWS:
            raise EnvironmentError("SAPI 5 is only available on Windows")

        super(SAPI5, self).__init__(*args, **kwargs)

        # win32com and pythoncom are Windows only, pylint:disable=import-error

        import win32com.client
        self._client = win32com.client

        import pythoncom
        self._pythoncom = pythoncom

        # pylint:enable=import-error

        voices = self._client.Dispatch('SAPI.SpVoice').getVoices()
        self._voice_map = {
            voice.getAttribute('name'): voice
            for voice in [voices.item(i) for i in range(voices.count)]
        }

        if not self._voice_map:
            raise EnvironmentError("No voices returned by SAPI 5")

    def desc(self):
        """
        Returns a short, static description.
        """

        count = len(self._voice_map)
        return ("SAPI 5.0 via win32com (%d %s)" %
                (count, "voice" if count == 1 else "voices"))

    def options(self):
        """
        Provides access to voice, speed, and volume.
        """

        voice_lookup = dict([
            # normalized with characters w/ diacritics stripped
            (self.normalize(voice[0]), voice[0])
            for voice in self._voice_map.keys()
        ] + [
            # normalized with diacritics converted
            (self.normalize(self.util_approx(voice[0])), voice[0])
            for voice in self._voice_map.keys()
        ])

        def transform_voice(value):
            """Normalize and attempt to convert to official voice."""

            normalized = self.normalize(value)

            return (
                voice_lookup[normalized] if normalized in voice_lookup
                else value
            )

        return [
            dict(
                key='voice',
                label="Voice",
                values=[(voice, voice)
                        for voice in sorted(self._voice_map.keys())],
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
        Writes a temporary wave file, and then transcodes to MP3.
        """

        output_wav = self.path_temp('wav')
        self._pythoncom.CoInitializeEx(self._pythoncom.COINIT_MULTITHREADED)

        try:
            stream = self._client.Dispatch('SAPI.SpFileStream')
            stream.open(output_wav, 3)  # 3=SSFMCreateForWrite

            try:
                speech = self._client.Dispatch('SAPI.SpVoice')
                speech.AudioOutputStream = stream
                speech.Rate = options['speed']
                speech.Voice = self._voice_map[options['voice']]
                speech.Volume = options['volume']
                speech.speak(text)
            finally:
                stream.close()

            self.cli_transcode(
                output_wav,
                path,
                require=dict(
                    size_in=4096,
                ),
            )

        finally:
            self._pythoncom.CoUninitialize()
            self.path_unlink(output_wav)

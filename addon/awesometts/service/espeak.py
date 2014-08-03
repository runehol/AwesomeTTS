# -*- coding: utf-8 -*-
# pylint:disable=bad-continuation

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
Service implementation for eSpeak text-to-speech engine
"""

__all__ = ['ESpeak']

from .base import Service
from .common import Trait


class ESpeak(Service):
    """
    Provides a Service-compliant implementation for eSpeak.
    """

    __slots__ = [
        '_binary',        # path to the eSpeak binary
        '_voice_list',    # list of installed voices as a list of tuples
        '_voice_lookup',  # map of normalized voice names to official names
    ]

    NAME = "eSpeak"

    TRAITS = [Trait.TRANSCODING]

    def __init__(self, *args, **kwargs):
        """
        Attempts to locate the eSpeak binary and read the list of voices
        from the `espeak --voices` output. If running on Windows, the
        registry will be searched to attempt to locate the eSpeak binary
        if it is not already in the path.

        eSpeak is a little unique in that it will accept a wide array of
        things with its --voices parameter, such as language (e.g. es),
        country-specific language (e.g. es-mx), or a specific voice file
        name (e.g. mexican-mbrola-1). It is also unique in that it has
        one list of native voices and another list of MBROLA voices.

        For our purposes, we use the voice names as the official driver
        of the 'voice' option, but we accept and remap the top-level and
        country-specific language codes to the "official" voice names.
        """

        super(ESpeak, self).__init__(*args, **kwargs)

        self._binary = 'espeak'

        try:
            es_output = self.cli_output(self._binary, '--voices')

        except OSError:
            if self.IS_WINDOWS:
                self._binary = r'%s\command_line\%s.exe' % (
                    self.reg_hklm(
                        r'Software\Microsoft\Speech\Voices\Tokens\eSpeak',
                        'Path',
                    ),
                    self._binary,
                )
                es_output = self.cli_output(self._binary, '--voices')

            else:
                raise

        mb_output = self.cli_output(self._binary, '--voices=mb')

        import re
        re_voice = re.compile(r'^\s*\d+\s+((\w+)[-\w]*)\s+([-\w])\s+([-\w]+)')

        es_matches = [
            match
            for match in [re_voice.match(line) for line in es_output]
            if match
        ]

        mb_matches = [
            match
            for match in [re_voice.match(line) for line in mb_output]
            if match
        ]

        self._voice_list = sorted([
            (
                match.group(4),

                "%s (%s%s)" % (
                    match.group(4),
                    'male ' if match.group(3).upper() == 'M'
                    else 'female ' if match.group(3).upper() == 'F'
                    else '',
                    match.group(1),
                ),
            )
            for match in es_matches + mb_matches
        ], key=lambda voice: voice[1].lower())

        if not self._voice_list:
            raise EnvironmentError("No usable output from `espeak --voices`")

        # provide various alternative voice inputs; unlike most other
        # services, we handle this setup in init so that we have access to the
        # regex match objects, which dictate the relative precedence
        self._voice_lookup = dict([
            # start with aliases for MBROLA top-level languages (e.g. es)
            (self.normalize(match.group(2)), match.group(4))
            for match in mb_matches
        ] + [
            # then add/override for MBROLA country languages (e.g. es-mx)
            (self.normalize(match.group(1)), match.group(4))
            for match in mb_matches
        ] + [
            # then add/override with native top-level languages (e.g. es)
            (self.normalize(match.group(2)), match.group(4))
            for match in es_matches
        ] + [
            # then add/override for native country languages (e.g. es-mx)
            (self.normalize(match.group(1)), match.group(4))
            for match in es_matches
        ] + [
            # then add/override for official voices (e.g. mexican-mbrola-1)
            (self.normalize(voice[0]), voice[0])
            for voice in self._voice_list
        ])

    def desc(self):
        """
        Returns a version string, terse description, and the TTS data
        location from `espeak --version`.
        """

        return "%s (%d voices)" % (
            self.cli_output(self._binary, '--version').pop(0),
            len(self._voice_list),
        )

    def options(self):
        """
        Provides access to voice, speed, word gap, pitch, and volume.
        """

        voice_lookup = self._voice_lookup

        def transform_voice(value):
            """Normalize and attempt to convert to official voice."""

            normalized = self.normalize(value)
            if normalized in voice_lookup:
                return voice_lookup[normalized]

            # if input is more than two characters, maybe the user was trying
            # a country-specific code (e.g. es-mx); chop it off and try again
            if len(normalized) > 2:
                if len(normalized) > 3:  # try the 3-character version first
                    normalized = normalized[0:3]
                    if normalized in voice_lookup:
                        return voice_lookup[normalized]

                normalized = normalized[0:2]
                if normalized in voice_lookup:
                    return voice_lookup[normalized]

            return value

        return [
            dict(
                key='voice',
                label="Voice",
                values=self._voice_list,
                transform=transform_voice,
            ),

            dict(
                key='speed',
                label="Speed",
                values=(80, 450, "wpm"),
                transform=int,
                default=175,
            ),

            dict(
                key='gap',
                label="Word Gap",
                values=(0.0, 5.0, "seconds"),
                transform=float,
                default=0.0,
            ),

            dict(
                key='pitch',
                label="Pitch",
                values=(0, 99, "%"),
                transform=int,
                default=50,
            ),

            dict(
                key='volume',
                label="Volume",
                values=(0, 200),
                transform=int,
                default=100,
            ),
        ]

    def run(self, text, options, path):
        """
        Checks for unicode workaround on Windows, writes a temporary
        wave file, and then transcodes to MP3.
        """

        input_file = self.path_workaround(text)
        output_wav = self.path_temp('wav')

        try:
            self.cli_call(
                [
                    self._binary,
                    '-v', options['voice'],
                    '-s', options['speed'],
                    '-g', int(options['gap'] * 100.0),
                    '-p', options['pitch'],
                    '-a', options['volume'],
                    '-w', output_wav,
                ] + (
                    ['-f', input_file] if input_file
                    else ['--', text]
                )
            )

            self.cli_transcode(
                output_wav,
                path,
                require=dict(
                    size_in=4096,
                ),
            )

        finally:
            self.path_unlink(input_file, output_wav)

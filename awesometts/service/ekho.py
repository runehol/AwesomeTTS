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
Service implementation for Ekho text-to-speech engine
"""

__all__ = ['Ekho']

from .base import Service
from .common import Trait


class Ekho(Service):
    """
    Provides a Service-compliant implementation for Ekho.
    """

    __slots__ = [
        '_voice_list',    # list of installed voices as a list of tuples
        '_voice_lookup',  # map of normalized voice names to official names
    ]

    NAME = "Ekho"

    TRAITS = [Trait.TRANSCODING]

    def __init__(self, *args, **kwargs):
        """
        Attempts to read the list of voices from the `ekho --help`
        output.
        """

        super(Ekho, self).__init__(*args, **kwargs)

        output = self.cli_output('ekho', '--help')

        import re
        re_list = re.compile(r'(language|voice).+available', re.IGNORECASE)
        re_voice = re.compile(r"'(\w+)'")

        self._voice_list = sorted({
            (capture, capture)
            for line in output if re_list.search(line)
            for capture in re_voice.findall(line)
        }, key=lambda voice: voice[1].lower())

        if not self._voice_list:
            raise EnvironmentError("No usable output from `ekho --help`")

        self._voice_lookup = {
            self.normalize(voice[0]): voice[0]
            for voice in self._voice_list
        }

    def desc(self):
        """
        Returns a simple version using `ekho --version`.
        """

        return "ekho %s" % self.cli_output('ekho', '--version').pop(0)

    def options(self):
        """
        Provides access to voice, speed, pitch, rate, and volume.
        """

        def transform_voice(value):
            """Normalize and attempt to convert to official voice."""

            normalized = self.normalize(value)
            normalized = (
                'mandarin' if normalized in [
                    'cmn', 'cosc', 'goyu', 'huyu', 'mand', 'zh', 'zhcn',
                ]
                else 'cantonese' if normalized in [
                    'cant', 'guzh', 'yue', 'yyef', 'zhhk', 'zhyue',
                ]
                else 'hakka' if normalized in ['hak', 'hakk', 'kejia']
                else 'tibetan' if normalized in ['cent', 'west']
                # else 'ngangien' if normalized in []
                else 'hangul' if normalized in ['ko', 'kor', 'kore', 'korean']
                else normalized
            )

            return (
                self._voice_lookup[normalized]
                if normalized in self._voice_lookup
                else value
            )

        voice_option = dict(
            key='voice',
            label="Voice",
            values=self._voice_list,
            transform=transform_voice,
        )

        if 'mandarin' in self._voice_lookup:
            voice_option['default'] = self._voice_lookup['mandarin']

        return [
            voice_option,

            dict(
                key='speed',
                label="Speed Delta",
                values=(-50, 300, "%"),
                transform=int,
                default=0,
            ),

            dict(
                key='pitch',
                label="Pitch Delta",
                values=(-100, 100, "%"),
                transform=int,
                default=0,
            ),

            dict(
                key='rate',
                label="Rate Delta",
                values=(-50, 100, "%"),
                transform=int,
                default=0,
            ),

            dict(
                key='volume',
                label="Volume Delta",
                values=(-100, 100, "%"),
                transform=int,
                default=0,
            ),
        ]

    def run(self, text, options, path):
        """
        Checks for unicode workaround on Windows, writes a temporary
        wave file, and then transcodes to MP3.

        Technically speaking, Ekho supports writing directly to MP3, but
        by going through LAME, we can apply the user's custom flags.
        """

        input_file = self.path_workaround(text)
        output_wav = self.path_temp('wav')

        self.cli_call(
            [
                'ekho',
                '-v', options['voice'],
                '-s', options['speed'],
                '-p', options['pitch'],
                '-r', options['rate'],
                '-a', options['volume'],
                '-o', output_wav,
            ] + (
                ['-f', input_file] if input_file
                else ['--', text]
            )
        )

        self.cli_transcode(output_wav, path)

        self.path_unlink(input_file, output_wav)

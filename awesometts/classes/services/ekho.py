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
        '_voices',   # list of installed voices as a list of tuples
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

        self._voices = sorted({
            (capture, capture)
            for line in output if re_list.search(line)
            for capture in re_voice.findall(line)
        })

        if not self._voices:
            raise EnvironmentError("No usable output from `ekho --help`")

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
            """
            Do some basic conversions to attempt to guess the language
            the user wanted when dealing with values that are not
            strictly correct for Ekho to process.
            """

            value = ''.join(char.lower() for char in value if char.isalpha())

            return (
                'Mandarin' if value in [
                    'cmn', 'cosc', 'goyu', 'huyu', 'mand', 'zh', 'zhcn',
                ]
                else 'Cantonese' if value in [
                    'cant', 'guzh', 'yue', 'yyef', 'zhhk', 'zhyue',
                ]
                else 'Hakka' if value in ['hak', 'hakk', 'kejia']
                else 'Tibetan' if value in ['cent', 'west']
                # else 'Ngangien' if value in []
                else 'Hangul' if value in ['ko', 'kor', 'kore', 'korean']
                else value[0].upper() + value[1:].lower() if len(value) > 1
                else value
            )

        return [
            dict(
                key='voice',
                label="Voice",
                values=self._voices,
                transform=transform_voice,
                default='Mandarin',
            ),

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

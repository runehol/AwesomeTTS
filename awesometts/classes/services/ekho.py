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


class Ekho(Service):
    """
    Provides a Service-compliant implementation for Ekho.
    """

    __slots__ = [
        '_voices',  # list of installed voices as a list of tuples
    ]

    @classmethod
    def desc(cls):
        return u"Ekho (余音) Chinese/Korean TTS Engine"

    def __init__(self, *args, **kwargs):
        """
        Attempt to read the list of voices from the `ekho --help`
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

    def options(self):
        """
        Provides access to voice, speed, pitch, rate, and volume.
        """

        return [
            dict(
                key='voice',
                label="Voice",
                options=self._voices,
            ),

            dict(
                key='speed',
                label="Speed Delta",
                options=[(i, "%d%%" % i) for i in range(-50, 301, 25)],
                default=0,
            ),

            dict(
                key='pitch',
                label="Pitch Delta",
                options=[(i, "%d%%" % i) for i in range(-100, 101, 25)],
                default=0,
            ),

            dict(
                key='rate',
                label="Rate Delta",
                options=[(i, "%d%%" % i) for i in range(-50, 101, 25)],
                default=0,
            ),

            dict(
                key='volume',
                label="Volume Delta",
                options=[(i, "%d%%" % i) for i in range(-100, 101, 25)],
                default=0,
            ),
        ]

    def run(self, text, options, path):
        """
        Check for unicode workaround on Windows, write a temporary wave
        file, and then transcode to MP3.

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

        self.unlink(input_file, output_wav)

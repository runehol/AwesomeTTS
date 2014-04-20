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
Service implementation for eSpeak voice engine
"""

__all__ = ['ESpeak']

from .base import Service


class ESpeak(Service):
    """
    Provides discovery, playback, and recording for eSpeak.
    """

    __slots__ = [
        '_binary',  # path to the eSpeak binary
        '_voices',  # list of installed voices as a list of tuples
    ]

    @classmethod
    def desc(cls):

        return "eSpeak Speech Synthesizer"

    def __init__(self, *args, **kwargs):
        """
        Attempt to locate the eSpeak binary and read the list of voices
        from the `espeak --voices` output.
        """

        super(ESpeak, self).__init__(*args, **kwargs)

        try:
            self._binary = 'espeak'
            output = self.cli_output(self._binary, '--voices')

        except self.NotFoundError:
            if self.WINDOWS:
                try:
                    self._binary = r'%s\command_line\%s.exe' % (
                        self.reg_hklm(
                            r'Software\Microsoft\Speech\Voices\Tokens\eSpeak',
                            'Path',
                        ),
                        self._binary,
                    )
                    output = self.cli_output(self._binary, '--voices')

                except self.NotFoundError:
                    raise self.UnavailableError

            else:
                raise self.UnavailableError

        import re
        re_voice = re.compile(r'^\s*(\d+\s+)?([-\w]+)(\s+[-\w]\s+([-\w]+))?')

        self._voices = sorted([
            (
                match.group(2),

                "%s (%s)" % (match.group(4), match.group(2)) if match.group(4)
                else match.group(2),
            )
            for match in [re_voice.match(line) for line in output]
            if match and match.group(2) != 'Pty'
        ], key=lambda voice: str.lower(voice[1]))

        if not self._voices:
            raise EnvironmentError("No usable output from `espeak --voices`")

    def options(self):
        """
        Provides access to voice, speed, word gap, pitch, and amplitude.
        """

        return [
            dict(
                key='voice',
                label="Voice",
                options=self._voices,
            ),

            dict(
                key='speed',
                label="Speed",
                options=[(i, "%d wpm" % i) for i in range(100, 451, 25)],
                default=175,
            ),

            dict(
                key='gap',
                label="Additional Word Gap",
                options=[(i, "%d ms" % (i * 10)) for i in range(0, 76, 25)] +
                    [(i, "%d sec" % (i / 100)) for i in range(100, 501, 100)],
                default=0,
            ),

            dict(
                key='pitch',
                label="Pitch",
                options=[(i, "%d%%" % i) for i in range(5, 96, 5)],
                default=50,
            ),

            dict(
                key='amp',
                label="Amplitude",
                options=[(i, "%d" % i) for i in range(0, 201, 25)],
                default=100,
            ),
        ]

    def play(self, text, options):
        """
        TODO
        """

        pass

    def record(self, text, options):
        """
        TODO
        """

        pass

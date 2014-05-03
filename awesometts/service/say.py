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
Service implementation for OS X's say command
"""

__all__ = ['Say']

from .base import Service
from .common import Trait


class Say(Service):
    """
    Provides a Service-compliant implementation for OS X's say command.
    """

    __slots__ = [
        '_binary',  # path to the eSpeak binary
        '_voices',  # list of installed voices as a list of tuples
    ]

    NAME = "Mac OS X Say"

    TRAITS = [Trait.TRANSCODING]

    def __init__(self, *args, **kwargs):
        """
        Attempts to read the list of voices from `say -v ?`.

        However, if not running on Mac OS X, no environment inspection
        is attempted and an exception is immediately raised.
        """

        if not self.IS_MACOSX:
            raise EnvironmentError("Say is only available on Mac OS X")

        super(Say, self).__init__(*args, **kwargs)

        # n.b. voices *can* have spaces; optionally also capture language code
        import re
        re_voice = re.compile(r'^\s*([-\w]+( [-\w]+)*)(\s+([-\w]+))?')

        self._voices = sorted([
            (
                match.group(1).lower(),

                "%s (%s)" % (match.group(1), match.group(4).replace('_', '-'))
                if match.group(4)
                else match.group(1),
            )
            for match in [
                re_voice.match(line)
                for line in self.cli_output('say', '-v', '?')
            ]
            if match
        ])

        if not self._voices:
            raise EnvironmentError("No usable output from call to `say -v ?`")

    def desc(self):
        """
        Returns a short, static description.
        """

        return "Mac OS X Say Command"

    def options(self):
        """
        Provides access to voice only.
        """

        return [
            dict(
                key='voice',
                label="Voice",
                values=self._voices,
                transform=lambda value: str(value).strip().lower(),
            ),

            dict(
                key='speed',
                label="Speed",
                values=(10, 500, "wpm"),
                transform=int,
                default=175,
            ),
        ]

    def run(self, text, options, path):
        """
        Writes a temporary AIFF file and then transcodes to MP3.
        """

        output_aiff = self.path_temp('aiff')

        self.cli_call(
            'say',
            '-v', options['voice'],
            '-r', options['speed'],
            '-o', output_aiff,
            text,
        )

        self.cli_transcode(output_aiff, path)

        self.path_unlink(output_aiff)
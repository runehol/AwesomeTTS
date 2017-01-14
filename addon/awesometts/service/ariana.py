# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
# Copyright (C) 2010-Present  Anki AwesomeTTS Development Team
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
Service implementation for Ariana's text-to-speech API
"""

from .base import Service
from .common import Trait

__all__ = ['Ariana']


class Ariana(Service):
    """
    Provides a Service-compliant implementation for Ariana.
    """

    __slots__ = [
    ]

    NAME = "Ariana"

    TRAITS = [Trait.INTERNET]

    VOICES = {
        'Female1': ('fa-IR', 'female'),
        'Male1': ('fa-IR', 'male'),
    }

    def desc(self):
        """
        Returns a short, static description.
        """

        return "Ariana text-to-speech Demo " \
            "(%d voices)" % len(self.VOICES)

    def options(self):
        """
        Provides access to voice and quality.
        """
        voice_lookup = {self.normalize(api_name): api_name
                        for api_name in self.VOICES.keys()}

        def transform_voice(user_value):
            """Fixes whitespace and casing only."""
            normalized_value = self.normalize(user_value)
            return (voice_lookup[normalized_value]
                    if normalized_value in voice_lookup else user_value)

        return [
            dict(key='voice',
                 label="Voice",
                 values=[(api_name,
                          "%s (%s %s)" % (api_name, gender, language))
                         for api_name, (language, gender)
                         in sorted(self.VOICES.items(),
                                   key=lambda item: (item[1][0],
                                                     item[1][1]))],
                 transform=transform_voice),

            dict(key='volume',
                 label="Volume",
                 values=(1, 5),
                 transform=lambda i: min(max(1, int(round(float(i)))), 5),
                 default=3),

            dict(key='speed',
                 label="Speed",
                 values=(1, 5),
                 transform=lambda i: min(max(1, int(round(float(i)))), 5),
                 default=3),

            dict(key='pitch',
                 label="Pitch",
                 values=(1, 10),
                 transform=lambda i: min(max(1, int(round(float(i)))), 10),
                 default=4),
        ]


    def run(self, text, options, path):
        """
        Downloads from Ariana directly to an MP3.

        Ariana will occasionally fail by returning a tiny MP3 file. If this
        happens, we retry the download (for a total of five tries).
        """

        def download():
            """Attempt a download of the given phrase."""
            self.net_download(
                path,
                [
                    ('http://api.farsireader.com/ArianaCloudService/ReadTextGET', dict(
                        APIKey='demo',
                        Text=subtext,
                        Speaker=options['voice'],
                        Format='mp3/32/m',
                        GainLevel=options['volume'],
                        PitchLevel=options['pitch'],
                        PunctuationLevel='2',
                        SpeechSpeedLevel=options['speed'],
                        ToneLevel=10,
                    ))

                    # n.b. limit seems to be much higher than 750, but this is
                    # a safe place to start (the web UI limits the user to 100)
                    for subtext in self.util_split(text, 750)
                ],
                require=dict(mime='audio/mpeg', size=1024),
                add_padding=True,
            )

        # TODO: This workaround is just fine for now, but it would be nice if
        # it were part of the net_download() call. That way, net_download()
        # could retry just the single segment that failed if the user is
        # playing back a long multi-segment phrase.

        for _ in range(5):
            try:
                download()
            except self.TinyDownloadError:
                pass
            else:
                break

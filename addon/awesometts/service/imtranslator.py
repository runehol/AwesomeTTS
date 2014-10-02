# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2014       Anki AwesomeTTS Development Team
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
Service implementation for ImTranslator's text-to-speech portal
"""

__all__ = ['ImTranslator']

import re

from .base import Service
from .common import Trait


class ImTranslator(Service):
    """
    Provides a Service-compliant implementation for ImTranslator.
    """

    __slots__ = []

    NAME = "ImTranslator"

    TRAITS = [Trait.INTERNET, Trait.TRANSCODING]

    _VOICES = [('Stefan', 'de', 'male'), ('VW Paul', 'en', 'male'),
               ('VW Kate', 'en', 'female'), ('Jorge', 'es', 'male'),
               ('Florence', 'fr', 'female'), ('Matteo', 'it', 'male'),
               ('VW Misaki', 'ja', 'female'), ('VW Yumi', 'ko', 'female'),
               ('Gabriela', 'pt', 'female'), ('Olga', 'ru', 'female'),
               ('VW Lily', 'zh', 'female')]

    _RE_SWF = re.compile(r'https?:[\w:/\.]+\.swf\?\w+=\w+', re.IGNORECASE)

    def desc(self):
        """
        Returns a short, static description.
        """

        return "ImTranslator text-to-speech web portal (%d voices)" % \
               len(self._VOICES)

    def options(self):
        """
        Provides access to voice and speed.
        """

        voice_lookup = dict([
            # language codes with full genders
            (self.normalize(code + gender), name)
            for name, code, gender in self._VOICES
        ] + [
            # language codes with first character of genders
            (self.normalize(code + gender[0]), name)
            for name, code, gender in self._VOICES
        ] + [
            # bare language codes
            (self.normalize(code), name)
            for name, code, gender in self._VOICES
        ] + [
            # official voice names
            (self.normalize(name), name)
            for name, code, gender in self._VOICES
        ])

        def transform_voice(value):
            """Normalize and attempt to convert to official name."""

            normalized = self.normalize(value)
            if normalized in voice_lookup:
                return voice_lookup[normalized]

            # if input is more than two characters, maybe the user was trying
            # a country-specific code (e.g. en-US); chop it off and try again
            if len(normalized) > 2:
                normalized = normalized[0:2]
                if normalized in voice_lookup:
                    return voice_lookup[normalized]

            return value

        return [
            dict(
                key='voice',
                label="Voice",
                values=[
                    (name, "%s (%s %s)" % (name, gender, code))
                    for name, code, gender in self._VOICES
                ],
                transform=transform_voice,
            ),

            dict(
                key='speed',
                label="Speed",
                values=(-10, 10),
                transform=int,
                default=0,
            ),
        ]

    def run(self, text, options, path):
        """
        Sends the TTS request to ImTranslator, captures the audio from
        the returned SWF, and transcodes to MP3.
        """

        payload = self.net_stream(
            ('http://imtranslator.net/translate-and-speak/sockets/tts.asp',
             dict(text=text,  # FIXME ideally, these would go over POST
                  vc=options['voice'],
                  speed=options['speed'],
                  FA=1)),
            require=dict(mime='text/html', size=256),
        )

        match = self._RE_SWF.search(payload)
        if not match or not match.group():
            raise EnvironmentError("Cannot find audio SWF in response from "
                                   "ImTranslator")
        swf = match.group()

        output_wav = self.path_temp('wav')

        try:
            self.net_dump(output_wav, swf)
            self.cli_transcode(output_wav, path, require=dict(size_in=4096))

        finally:
            self.path_unlink(output_wav)

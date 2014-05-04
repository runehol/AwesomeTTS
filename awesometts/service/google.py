# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2013-2014  Dave Shifflett
# Copyright (C) 2013       mistaecko on GitHub
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
Service implementation for Google Translate's text-to-speech API
"""

__all__ = ['Google']

from .base import Service
from .common import Trait


class Google(Service):
    """
    Provides a Service-compliant implementation for Google Translate.
    """

    __slots__ = [
    ]

    NAME = "Google Translate"

    TRAITS = [Trait.INTERNET]

    def desc(self):
        """
        Returns a short, static description.
        """

        return "Google Translate text-to-speech web API"

    def options(self):
        """
        Provides access to voice only.
        """

        voice_codes = {
            'af': "Afrikaans", 'ar': "Arabic", 'bs': "Bosnian",
            'ca': "Catalan", 'cs': "Czech", 'cy': "Welsh", 'da': "Danish",
            'de': "German", 'el': "Greek", 'en': "English", 'eo': "Esperanto",
            'es': "Spanish", 'fi': "Finnish", 'fr': "French", 'hi': "Hindi",
            'hr': "Croatian", 'ht': "Haitian Creole", 'hu': "Hungarian",
            'hy': "Armenian", 'id': "Indonesian", 'is': "Icelandic",
            'it': "Italian", 'ja': "Japanese", 'ko': "Korean", 'la': "Latin",
            'lv': "Latvian", 'mk': "Macedonian", 'nl': "Dutch",
            'no': "Norwegian", 'pl': "Polish", 'pt': "Portuguese",
            'ro': "Romanian", 'ru': "Russian", 'sk': "Slovak",
            'sq': "Albanian", 'sr': "Serbian", 'sv': "Swedish",
            'sw': "Swahili", 'ta': "Tamil", 'th': "Thai", 'tr': "Turkish",
            'vi': "Vietnamese", 'zh': "Chinese",
        }

        voice_list = sorted([
            (code, "%s (%s)" % (name, code))
            for code, name in voice_codes.items()
        ], key=lambda voice: voice[1])

        voice_lookup = dict([
            (self.normalize(name), code)
            for code, name in voice_codes.items()
        ] + [
            (self.normalize(code), code)
            for code in voice_codes.keys()
        ])

        def transform_voice(value):
            """Normalize and attempt to convert to official code."""

            normalized = self.normalize(value)
            if normalized in voice_lookup:
                return voice_lookup[normalized]

            # if input is more than two characters, maybe the user was trying
            # a country-specific code (e.g. es-mx); chop it off and try again
            if len(normalized) > 2:
                normalized = normalized[0:2]
                if normalized in voice_lookup:
                    return voice_lookup[normalized]

            return value

        return [
            dict(
                key='voice',
                label="Voice",
                values=voice_list,
                transform=transform_voice,
            ),
        ]

    def run(self, text, options, path):
        """
        Downloads from Google directly to an MP3.

        Because the MP3 get from Google is already so very tiny, LAME is
        not used for transcoding.
        """

        self.net_download(
            path=path,
            addr='http://translate.google.com/translate_tts',
            query=dict(
                tl=options['voice'],
                q=text,
            ),
            require=dict(
                status=200,
                mime='audio/mpeg',
            ),
        )

# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2015       Anki AwesomeTTS Development Team
# Copyright (C) 2015       Dave Shifflett
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
Service implementation for NeoSpeech's text-to-speech demo engine
"""

__all__ = ['NeoSpeech']

import json
import re
from socket import error as SocketError  # router does not cache this

from .base import Service
from .common import Trait


VOICES = [('en-GB', 'male', "Hugh", 33), ('en-GB', 'female', "Bridget", 4),
          ('en-US', 'male', "James", 10), ('en-US', 'male', "Paul", 1),
          ('en-US', 'female', "Ashley", 14), ('en-US', 'female', "Julie", 3),
          ('en-US', 'female', "Kate", 2), ('es-MX', 'male', "Francisco", 31),
          ('es-MX', 'female', "Gloria", 32), ('es-MX', 'female', "Violeta", 5),
          ('fr-CA', 'female', "Chloe", 13), ('ja', 'male', "Ryo", 28),
          ('ja', 'male', "Show", 8), ('ja', 'male', "Takeru", 30),
          ('ja', 'female', "Haruka", 26), ('ja', 'female', "Hikari", 29),
          ('ja', 'female', "Misaki", 9), ('ja', 'female', "Sayaka", 27),
          ('ko', 'male', "Jihun", 21), ('ko', 'male', "Junwoo", 6),
          ('ko', 'female', "Dayoung", 17), ('ko', 'female', "Hyeryun", 18),
          ('ko', 'female', "Hyuna", 19), ('ko', 'female', "Jimin", 20),
          ('ko', 'female', "Sena", 22), ('ko', 'female', "Yumi", 7),
          ('ko', 'female', "Yura", 23), ('zh', 'male', "Liang", 12),
          ('zh', 'male', "Qiang", 25), ('zh', 'female', "Hong", 24),
          ('zh', 'female', "Hui", 11)]

MAP = {name: api_id for language, gender, name, api_id in VOICES}


class NeoSpeech(Service):
    """
    Provides a Service-compliant implementation for NeoSpeech.
    """

    __slots__ = [
        '_busy',     # limit concurrent runs (download URL is tied to cookie)
        '_cookies',  # used for all NeoSpeech requests in this Anki session
    ]

    NAME = "NeoSpeech"

    TRAITS = [Trait.INTERNET]

    def __init__(self, *args, **kwargs):
        self._busy = False
        self._cookies = None
        super(NeoSpeech, self).__init__(*args, **kwargs)

    def desc(self):
        """Returns name with a voice count."""

        return "NeoSpeech Demo (%d voices)" % len(VOICES)

    def options(self):
        """Provides access to voice only."""

        def transform_voice(value):
            # TODO
            return value

        return [dict(key='voice',
                     label="Voice",
                     values=[(name, "%s (%s %s)" % (name, gender, language))
                             for language, gender, name, api_id in VOICES],
                     transform=transform_voice)]

    def run(self, text, options, path):
        """Requests MP3 URLs and then downloads them."""

        if self._busy:
            raise SocketError("NeoSpeech does not allow concurrent runs. If "
                              "you need to playback multiple phrases at the "
                              "same time, please consider using a different "
                              "service.")
        self._busy = True

        try:
            if not self._cookies:
                headers = self.net_headers('http://neospeech.com')
                self._cookies = ';'.join(
                    cookie.split(';')[0]
                    for cookie in headers['Set-Cookie'].split(',')
                )
            headers = {'Cookie': self._cookies}

            # TODO handle long content (similar pattern as ImTranslator?)

            url = self.net_stream(
                ('http://neospeech.com/service/demo',
                  dict(voiceId=MAP[options['voice']], content=text)),
                custom_headers=headers,
            )
            url = json.loads(url)
            url = url['audioUrl']
            assert len(url) > 1 and url[0] == '/', "expecting relative URL"

            self.net_download(path,
                              'http://neospeech.com' + url,
                              require=dict(mime='audio/mpeg', size=256),
                              custom_headers=headers)

        finally:
            self._busy = False

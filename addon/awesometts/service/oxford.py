# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2015       Anki AwesomeTTS Development Team
# Copyright (C) 2015       Myrgy on GitHub
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
Service implementation for Oxford Dictionary
"""

__all__ = ['Oxford']

from .base import Service
from .common import Trait

import urllib

from HTMLParser import HTMLParser

class OxfordLister(HTMLParser):
	def reset(self):
        	HTMLParser.reset(self)
		self.sounds = []

	def handle_starttag(self, tag, attrs):
		snd = [v for k, v in attrs if k=='data-src-mp3']
		if snd:
			self.sounds.extend(snd)

class Oxford(Service):
    """
    Provides a Service-compliant implementation for Oxford Dictionary.
    """

    __slots__ = []

    NAME = "Oxford Dictionary"

    TRAITS = [Trait.INTERNET]

    _VOICE_CODES = {
        # n.b. When modifying any variants, make sure that there are
        # aliases defined in the voice_lookup list below for the most
        # common alternate codes, including an alias from the base
        # language to the variant with the most native speakers.

        'en-GB': "English, British", 'en-US': "English, American",
    }

    def desc(self):
        """
        Returns a short, static description.
        """

        return "Oxford Dictionary web API " \
            "(%d voices)" % len(self._VOICE_CODES)

    def options(self):
        """
        Provides access to voice only.
        """

        voice_lookup = dict([
            # aliases for English, British (moderate number)
            (self.normalize(alias), 'en-GB')
            for alias in ['en-EU', 'en-UK']
        ] + [
            # aliases for English, American (most speakers)
            (self.normalize(alias), 'en-US')
            for alias in ['English', 'en']
        ])

        def transform_voice(value):
            """Normalize and attempt to convert to official code."""
            normalized = self.normalize(value)
            if normalized in voice_lookup:
                return voice_lookup[normalized]
            return value

        return [
            dict(
                key='voice',
                label="Voice",
                values=[(code, "%s (%s)" % (name, code))
                        for code, name in sorted(self._VOICE_CODES.items())],
                transform=transform_voice,
            ),
        ]

    def run(self, text, options, path):
        """
        Download wep page for given word
        Then extract mp3 path and download it
        """

        dict_url = "http://www.oxforddictionaries.com/definition/"
        voice = options['voice']
        if (voice == 'en-US'):
            dict_url += "american_english/"
        else:
            dict_url += "english/"

        usock = urllib.urlopen(dict_url + text)
        parser = OxfordLister()
        parser.feed(usock.read())
        parser.close()
        usock.close()

        if len(parser.sounds) > 0:
            sound_url = parser.sounds[0]
        
            self.net_download(
                path,
                sound_url,
                require=dict(mime='audio/mpeg', size=1024),
             )
        else:
            raise IOError("sound not found: " + dict_url)

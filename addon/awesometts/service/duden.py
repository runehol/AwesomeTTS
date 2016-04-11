# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2016       Anki AwesomeTTS Development Team
# Copyright (C) 2016       Dave Shifflett
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
Service implementation for Duden
"""

from re import compile as re

from .base import Service
from .common import Trait

__all__ = ['Duden']


SEARCH_FORM = 'http://www.duden.de/suchen/dudenonline'
RE_DETAIL = re(r'href="(https?://www\.duden\.de/rechtschreibung/(.+?))"')
RE_MP3 = re(r'href="(https?://www\.duden\.de/_media_/audio/.+?\.mp3)"')


class Duden(Service):
    """
    Provides a Service-compliant implementation for Duden.
    """

    __slots__ = []

    NAME = "Duden"

    TRAITS = [Trait.INTERNET]

    def desc(self):
        """
        Returns a short, static description.
        """

        return "Duden (German only, single words only)"

    def options(self):
        """
        Advertises German, but does not allow any configuration.
        """

        return [
            dict(
                key='voice',
                label="Voice",
                values=[('de', "German (de)")],
                transform=lambda value: (
                    'de' if self.normalize(value).startswith('de')
                    else value
                ),
                default='de',
            ),
        ]

    def modify(self, text):
        """
        Transform any eszett or character with an umlaut to the ASCII
        form that Duden uses. Drop any other non-ASCII characters or
        non-alphabetic symbols. Retain spaces so we can display a "no
        multi-word input" error message if needed (so that in-order
        group can fallover to the next preset).
        """

        return ''.join(
            'Ae' if char == u'\u00c4'
            else 'Oe' if char == u'\u00d6'
            else 'Ue' if char == u'\u00dc'
            else 'sz' if char == u'\u00df'
            else 'ae' if char == u'\u00e4'
            else 'oe' if char == u'\u00f6'
            else 'ue' if char == u'\u00fc'
            else char
            for char in text
            if char.isalpha() or char == ' '
        ).strip().encode('us-ascii', errors='ignore')

    def run(self, text, options, path):
        """
        WIP
        """

        assert options['voice'] == 'de', "Only German is supported."

        if len(text) > 100:
            raise IOError("Your input text is too long for Duden.")

        if ' ' in text:
            raise IOError("You cannot use multiple words with Duden.")

        html = self.net_stream((SEARCH_FORM, dict(s=text)),
                               require=dict(mime='text/html'))

        seen_urls = {}
        candidates = []

        for match in RE_DETAIL.finditer(html):
            url = match.group(1)
            if url in seen_urls:
                continue
            seen_urls[url] = True

            word = match.group(2)

            if word == text:
                candidates.append((0, url))
                continue

            word_lower = word.lower()
            text_lower = text.lower()

            if word_lower == text_lower:
                candidates.append((1, url))
            elif word.split('_', 1)[0] == text:
                candidates.append((2, url))
            elif word_lower.split('_', 1)[0] == text_lower:
                candidates.append((3, url))

        for _, url in sorted(candidates):
            html = self.net_stream(url)
            match = RE_MP3.search(html)

            if match:
                self.net_download(path, match.group(1),
                                  require=dict(mime='audio/mpeg'))
                return

        raise IOError("Duden does not have recorded audio for this word.")

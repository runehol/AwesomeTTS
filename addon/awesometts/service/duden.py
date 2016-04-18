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

TODO: Improve performance. Can we skip certain detail URLs based on them
not possibly matching the input string? Maybe restore the eszett/umlaut
conversion in modify() and force URLs to begin with <input> or <input>_
... if we do that, then the eszett conversion in comparison_normalize()
can go away, because the input text string should already have taken care
of it, but make sure to test words with eszett

TODO: Make sure all imports safe on various Anki packages on OS X and on
Windows.

TODO: Needs lots of manual testing. Search for various words manually on
www.duden.de and make sure anything that has pronunciation works through
here, including making sure lookalikes (e.g. schon/schön) are done
correctly.
"""

from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParser
from re import compile as re
from unicodedata import normalize as unicode_normalize

from .base import Service
from .common import Trait

__all__ = ['Duden']


INPUT_MAXIMUM = 100
IGNORE_ARTICLES = ['der', 'das', 'die']
CASE_MATTERS = ['Weg']

SEARCH_FORM = 'http://www.duden.de/suchen/dudenonline'
RE_DETAIL = re(r'href="(https?://www\.duden\.de/rechtschreibung/.+?)"')
RE_MP3 = re(r'(Betonung:|Bei der Schreibung) '
            r'(<em>|&raquo;)(.+?)(</em>|&laquo;).+?'
            r'<a .*? href="(https?://www\.duden\.de/_media_/audio/.+?\.mp3)"')

HTML_PARSER = HTMLParser()


def comparison_normalize(input_string):
    """Throw away diacritics, accent marks, dashes, spaces, etc."""
    input_string = input_string.replace(' ', '').replace('-', '')
    input_string = input_string.replace(u'\u00df', 'ss')
    return unicode_normalize('NFKD', input_string).encode('ASCII', 'ignore')


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

        return "Duden (German only, single words and short phrases only)"

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
        Drop non-alphanumeric/non-space/non-dash characters, remove any
        leading or trailing dash on any individual word, remove any
        leading article from inputs with 2+ words, drop out extra
        whitespace, and force lowercase (unless exception like "Weg").
        """

        text = ''.join(char
                       for char in text
                       if char.isalpha() or char == ' ' or char == '-')

        words = text.split()
        words = [word.strip('-') for word in words]
        words = [word for word in words if word]

        if not words:
            return ''

        if len(words) > 1 and words[0].lower() in IGNORE_ARTICLES:
            words.pop(0)

        text = ''.join(words)

        if text not in CASE_MATTERS:
            text = text.lower()

        return text


    def run(self, text, options, path):
        """
        """

        assert options['voice'] == 'de', "Only German is supported."

        if len(text) > INPUT_MAXIMUM:
            raise IOError("Your input text is too long for Duden.")

        self._logger.debug('Duden: Searching on "%s"', text)
        try:
            html = self.net_stream((SEARCH_FORM, dict(s=text)),
                                   require=dict(mime='text/html'))
        except IOError as io_error:
            if getattr(io_error, 'code', None) == 404:
                raise IOError("Duden does not recognize this input.")
            else:
                raise

        text = comparison_normalize(text)
        self._logger.debug('Duden: Will use "%s" for comparisons', text)

        seen_urls = {}

        for match in RE_DETAIL.finditer(html):
            url = match.group(1)

            if url in seen_urls:
                continue
            seen_urls[url] = True

            self._logger.debug("Duden: Trying the entry at %s", url)
            html = self.net_stream(url)

            for match in RE_MP3.finditer(html):
                word = match.group(3)
                word = ''.join(HTML_PARSER.unescape(word)
                               for word
                               in BeautifulSoup(word).findAll(text=True))
                word = self.modify(word)
                word = comparison_normalize(word)

                url = match.group(5)

                if word == text:
                    self._logger.debug('Duden: Matched "%s" at %s', word, url)
                    self.net_download(path, url,
                                      require=dict(mime='audio/mpeg'))
                    return

                else:
                    self._logger.debug('Duden: Skipped "%s" at %s', word, url)

        raise IOError("Duden does not have recorded audio for this word.")

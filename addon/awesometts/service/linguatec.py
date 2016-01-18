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
Service implementation for Linguatec's text-to-speech demo engine
"""

from .base import Service
from .common import Trait

__all__ = ['Linguatec']


VOICES = {
    'Angelica': 'es-MX',
    'Carlos': 'es-CO',
    'Diego': 'es-AR',
    'Jorge': 'es',
    'Juan': 'es-MX',
    'Monica': 'es',
    'Paulina': 'es-MX',
    'Soledad': 'es-CO',

    # TODO
}


class Linguatec(Service):
    """
    Provides a Service-compliant implementation for Linguatec.
    """

    __slots__ = [
    ]

    NAME = "Linguatec"

    TRAITS = [Trait.INTERNET]

    def desc(self):
        """Returns name with a voice count."""

        return "Linguatec Demo (%d voices)" % len(VOICES)

    def options(self):
        """Provides access to voice only."""

        voice_lookup = {self.normalize(name): name for name in VOICES.keys()}

        def transform_voice(value):
            """Fixes whitespace and casing errors only."""
            normal = self.normalize(value)
            return voice_lookup[normal] if normal in voice_lookup else value

        return [dict(key='voice',
                     label="Voice",
                     values=[(name, "%s (%s)" % (name, language))
                             for name, language
                             in sorted(VOICES.items(),
                                       key=lambda item: (item[1], item[0]))],
                     transform=transform_voice)]

    def run(self, text, options, path):
        """Requests MP3 URLs and then downloads them."""

        pass

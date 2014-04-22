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

from .base import Service, Trait


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

        return [
            dict(
                key='voice',
                label="Voice",
                items=[
                    ('af', "Afrikaans (af)"),
                    ('sq', "Albanian (sq)"),
                    ('ar', "Arabic (ar)"),
                    ('hy', "Armenian (hy)"),
                    ('bs', "Bosnian (bs)"),
                    ('ca', "Catalan (ca)"),
                    ('zh', "Chinese (zh)"),
                    ('hr', "Croatian (hr)"),
                    ('cs', "Czech (cs)"),
                    ('da', "Danish (da)"),
                    ('nl', "Dutch (nl)"),
                    ('en', "English (en)"),
                    ('eo', "Esperanto (eo)"),
                    ('fi', "Finnish (fi)"),
                    ('fr', "French (fr)"),
                    ('de', "German (de)"),
                    ('el', "Greek (el)"),
                    ('ht', "Haitian Creole (ht)"),
                    ('hi', "Hindi (hi)"),
                    ('hu', "Hungarian (hu)"),
                    ('is', "Icelandic (is)"),
                    ('id', "Indonesian (id)"),
                    ('it', "Italian (it)"),
                    ('ja', "Japanese (ja)"),
                    ('ko', "Korean (ko)"),
                    ('la', "Latin (la)"),
                    ('lv', "Latvian (lv)"),
                    ('mk', "Macedonian (mk)"),
                    ('no', "Norwegian (no)"),
                    ('pl', "Polish (pl)"),
                    ('pt', "Portuguese (pt)"),
                    ('ro', "Romanian (ro)"),
                    ('ru', "Russian (ru)"),
                    ('sr', "Serbian (sr)"),
                    ('sk', "Slovak (sk)"),
                    ('es', "Spanish (es)"),
                    ('sw', "Swahili (sw)"),
                    ('sv', "Swedish (sv)"),
                    ('ta', "Tamil (ta)"),
                    ('th', "Thai (th)"),
                    ('tr', "Turkish (tr)"),
                    ('vi', "Vietnamese (vi)"),
                    ('cy', "Welsh (cy)"),
                ],
                normalize=lambda value: ''.join(
                    char.lower()
                    for char in value.split('-').pop(0)
                    if char.isalpha()
                ),
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

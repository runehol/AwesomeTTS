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
Service implementation for Google's TTS API
"""

__all__ = ['TTS_service']

from os.path import isfile
from subprocess import mswindows, Popen
import urllib, urllib2
from PyQt4 import QtCore
from awesometts import conf
from awesometts.paths import cache_path, temp_path
from awesometts.util import STARTUP_INFO


URL = 'http://translate.google.com/translate_tts'

# TODO Move this out to a class module responsible for downloads
PROXIES = urllib.getproxies()
if PROXIES and 'http' in PROXIES:
    URL = '/'.join([
        PROXIES['http'].replace('http:', 'http_proxy:').rstrip('/'),
        URL,
    ])

VOICES = [
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
]

SERVICE = 'g'


def _get_address(voice, text):
    from ..util import TO_ENCODED

    return ''.join([
        URL, '?tl=', voice, '&q=',
        urllib.quote_plus(TO_ENCODED(text), safe=''),
    ])

# TODO Move this out to a class module responsible for playback
def _mplayer_playback(address_or_path):
    if mswindows:
        param = [
            'mplayer.exe', '-slave',
            '-ao', 'win32',
            '-user-agent', 'Mozilla/5.0',
            address_or_path,
        ]

        if conf.subprocessing:
            Popen(param, startupinfo=STARTUP_INFO)
        else:
            Popen(param, startupinfo=STARTUP_INFO).wait()
    else:
        param = [
            'mplayer', '-slave',
            '-user-agent', 'Mozilla/5.0',
            address_or_path,
        ]

        if conf.subprocessing:
            Popen(param)
        else:
            Popen(param).wait()


# TODO Move this out to a class module responsible for downloads
class Downloader(object):
    had_network_error = False
    had_response_error = False
    threads = {}

    @staticmethod
    def fetch(address, path_mp3):
        for key in Downloader.threads.keys():
            if Downloader.threads[key].isFinished():
                del Downloader.threads[key]

        if not path_mp3 in Downloader.threads:
            Downloader.threads[path_mp3] = Worker(address, path_mp3)
            Downloader.threads[path_mp3].start()


# TODO Move this out to a class module responsible for downloads
class Worker(QtCore.QThread):
    def __init__(self, address, path_mp3):
        QtCore.QThread.__init__(self)
        self.address = address
        self.path_mp3 = path_mp3

    def run(self):
        try:
            response = urllib2.urlopen(
                urllib2.Request(
                    self.address,
                    headers={'User-Agent': 'Mozilla/5.0'},
                ),
                timeout=15,
            )

            if (
                response.getcode() == 200 and
                response.info().gettype() == 'audio/mpeg'
            ):
                with open(self.path_mp3, 'wb') as cache_output:
                    cache_output.write(response.read())
                response.close()

                _mplayer_playback(self.path_mp3)

            else:
                if not Downloader.had_response_error:
                    from sys import stderr

                    Downloader.had_response_error = True
                    stderr.write(
                        "The Google TTS API did not return an MP3.\n"
                        "%s\n"
                        "\n"
                        "If this persists, please open an issue at "
                        "<https://github.com/AwesomeTTS/AwesomeTTS/issues>.\n"
                        "\n"
                        "This will only be displayed once this session.\n" % (
                            self.address,
                        )
                    )

        except:  # allow recovery from any exception, pylint:disable=W0702
            if not Downloader.had_network_error:
                from sys import stderr
                from traceback import format_exc

                Downloader.had_network_error = True
                stderr.write(
                    "The download from the Google TTS API failed.\n"
                    "%s\n"
                    "\n"
                    "%s\n"
                    "\n"
                    "Check your network connectivity, or open an issue at "
                    "<https://github.com/AwesomeTTS/AwesomeTTS/issues>.\n"
                    "\n"
                    "This will only be displayed once this session.\n" % (
                        self.address,
                        format_exc(),
                    )
                )


def play(text, voice):
    address = _get_address(voice, text)

    if conf.caching:
        path_mp3 = cache_path(text, SERVICE, voice, 'mp3')

        if isfile(path_mp3):
            _mplayer_playback(path_mp3)

        else:
            Downloader.fetch(address, path_mp3)

    else:
        _mplayer_playback(address)

def record(text, voice):
    address = _get_address(voice, text)
    path_mp3 = temp_path(text, SERVICE, voice, 'mp3')

    if mswindows:
        Popen(
            [
                'mplayer.exe', '-slave',
                '-ao', 'win32',
                '-user-agent', 'Mozilla/5.0',
                address,
                '-dumpstream', '-dumpfile', path_mp3,
            ],
            startupinfo=STARTUP_INFO,
        ).wait()

    else:
        Popen([
            'mplayer', '-slave',
            '-user-agent', 'Mozilla/5.0',
            address,
            '-dumpstream', '-dumpfile', path_mp3,
        ]).wait()

    return path_mp3


TTS_service = {SERVICE: {
    'name': "Google",
    'play': play,
    'record': record,
    'voices': VOICES,
    'throttle': True,
}}

# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2015  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2013-2015  Dave Shifflett
# Copyright (C) 2013       mistaecko on GitHub
# Copyright (C) 2015       Glutanimate on GitHub
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

from socket import error as SocketError  # router does not cache this
from PyQt4.QtCore import QTimer, QUrl
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.QtWebKit import QWebPage

from .base import Service
from .common import Trait


HEADER_CONTENT_TYPE = QNetworkRequest.ContentTypeHeader
HEADER_CONTENT_LENGTH = QNetworkRequest.ContentLengthHeader
HEADER_LOCATION = QNetworkRequest.LocationHeader

LIMIT = 200

VOICES = {'af': "Afrikaans", 'ar': "Arabic", 'bs': "Bosnian", 'ca': "Catalan",
          'cs': "Czech", 'cy': "Welsh", 'da': "Danish", 'de': "German",
          'el': "Greek", 'en': "English", 'eo': "Esperanto", 'es': "Spanish",
          'fi': "Finnish", 'fr': "French", 'hi': "Hindi", 'hr': "Croatian",
          'ht': "Haitian Creole", 'hu': "Hungarian", 'hy': "Armenian",
          'id': "Indonesian", 'is': "Icelandic", 'it': "Italian",
          'ja': "Japanese", 'ko': "Korean", 'la': "Latin", 'lv': "Latvian",
          'mk': "Macedonian", 'nl': "Dutch", 'no': "Norwegian",
          'pl': "Polish", 'pt': "Portuguese", 'ro': "Romanian",
          'ru': "Russian", 'sk': "Slovak", 'sq': "Albanian",
          'sr': "Serbian", 'sv': "Swedish", 'sw': "Swahili", 'ta': "Tamil",
          'th': "Thai", 'tr': "Turkish", 'vi': "Vietnamese", 'zh': "Chinese"}

SCRIPT = '''
    setTimeout(function() {
        var listen = function() {
            var node = document.getElementById('gt-src-listen');
            if (node) {
                ['mousedown', 'mouseup'].forEach(function(type) {
                    var event = document.createEvent('MouseEvents');
                    event.initEvent(type, true, true);
                    node.dispatchEvent(event);
                });
            }
        };

        var fix = document.querySelector('.gt-revert-correct-message a');
        if (fix) {
            fix.click();
            setTimeout(listen, 1000 + Math.random() * 4000);
        } else {
            listen();
        }
    }, 1000 + Math.random() * 4000);
'''


class Google(Service):
    """
    Provides a Service-compliant implementation for Google Translate.
    """

    __slots__ = [
        '_nam',     # recycled QNetworkAccessManager instance for all requests
        '_page',    # recycled QWebPage instance for all requests
        '_frame',   # recycled QWebFrame instance for all requests
        '_cb',      # when a request is in-process, dict set to the callbacks
    ]

    NAME = "Google Translate"

    TRAITS = [Trait.INTERNET]

    def __init__(self, *args, **kwargs):
        self._nam = self._page = self._frame = self._cb = None
        super(Google, self).__init__(*args, **kwargs)

    def desc(self):
        """Returns voice count and character count limit."""

        return ("Google Translate text-to-speech web API (%d voices; "
                "limited to %d characters of input)\n"
                "\n"
                "Note that this service is slow and not generally "
                "recommended.") % (len(VOICES), LIMIT)

    def options(self):
        """Provides access to voice only."""

        voice_lookup = dict([(self.normalize(name), code)
                             for code, name in VOICES.items()] +
                            [(self.normalize(code), code)
                             for code in VOICES.keys()])

        def transform_voice(value):
            normalized = self.normalize(value)

            if normalized in voice_lookup:
                return voice_lookup[normalized]

            if len(normalized) > 2:
                normalized = normalized[0:2]
                if normalized in voice_lookup:
                    return voice_lookup[normalized]

            return value

        return [dict(key='voice',
                     label="Voice",
                     values=[(code, "%s (%s)" % (name, code))
                             for code, name in sorted(VOICES.items())],
                     transform=transform_voice)]

    def prerun(self, text, options, path, router_success, router_error):
        """Load Google Translate w/ language/text to capture audio."""

        if len(text) > LIMIT:
            raise IOError("Google Translate is limited to %d characters. "
                          "Consider using a different service if you need "
                          "playback for long phrases." % LIMIT)
        elif self._cb:
            raise SocketError("Google Translate does not allow concurrent "
                              "runs. If you need to playback multiple "
                              "phrases at the same time, please consider "
                              "using a different service.")

        if not self._frame:
            self._prerun_setup()

        self._netops += 30

        state = {}  # using a dict to workaround lack of `nonlocal` keyword
        def okay(stream):
            if 'resolved' not in state:
                state['resolved'] = True
                self._cb = None
                router_success(stream)
        def fail(message):
            if 'resolved' not in state:
                state['resolved'] = True
                self._cb = None
                router_error(SocketError(message))
        self._cb = dict(okay=okay, fail=fail)

        url = QUrl('https://translate.google.com/')
        url.addQueryItem('sl', options['voice'])
        url.addQueryItem('q', text)
        self._frame.load(url)

        def timeout():
            fail("Request timed out")
        QTimer.singleShot(15000, timeout)

    def _prerun_setup(self):
        """
        Sets up our web instances.

        This stuff is done here and called via `prerun()` rather than
        just being setup in `__init__()` because *in the event* that
        doing any of this crashes Qt or Anki, we do not want to trigger
        that by just having the user do anything with AwesomeTTS.
        """

        class InterceptingNAM(QNetworkAccessManager):
            def createRequest(nself, op, req, *args, **kwargs):
                if self._cb and '/translate_tts' in req.url().toString():
                    # FIXME: Does re-calling `createRequest()` cause two HTTP
                    # requests to go across the wire? If so, return a dummy
                    # object instead whenever we actually want to intercept it.
                    rep = QNetworkAccessManager.createRequest(nself, op, req,
                                                              *args, **kwargs)
                    def finished():
                        if not self._cb:
                            pass
                        if rep.error():
                            self._cb['fail']("error in network reply")
                        elif rep.header(HEADER_LOCATION):
                            self._cb['fail']("got redirected away")
                        elif rep.header(HEADER_CONTENT_TYPE) != 'audio/mpeg':
                            self._cb['fail']("unexpected Content-Type")
                        elif rep.header(HEADER_CONTENT_LENGTH) < 1024:
                            self._cb['fail']("Content-Length is too small")
                        else:
                            stream = rep.readAll()
                            if not stream:
                                self._cb['fail']("no stream returned")
                            elif len(stream) < 1024:
                                self._cb['fail']("stream is too small")
                            else:
                                self._cb['okay'](stream)
                    rep.finished.connect(finished)

                return QNetworkAccessManager.createRequest(nself, op, req,
                                                           *args, **kwargs)

        self._nam = nam = InterceptingNAM()

        self._page = page = QWebPage()
        page.setNetworkAccessManager(nam)

        self._frame = frame = page.mainFrame()
        def frame_load_finished(successful):
            if not self._cb:
                pass
            elif successful:
                frame.evaluateJavaScript(SCRIPT)
            else:
                self._cb['fail']("Cannot load Google Translate page")
        frame.loadFinished.connect(frame_load_finished)

    def run(self, text, options, path):
        """Grab the stream from our prerun and write it to disk."""

        with open(path, 'wb') as output:
            output.write(options['prerun'])
        self.util_pad(path)

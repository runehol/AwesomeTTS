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
            setTimeout(listen, 1000);
        } else {
            listen();
        }
    }, 1000);
'''


class Google(Service):
    """
    Provides a Service-compliant implementation for Google Translate.
    """

    __slots__ = [
        '_frames',  # maps in-flight QWebFrames to their callbacks
        '_nam',     # shared QNetworkAccessManager across all QWebPages
    ]

    NAME = "Google Translate"

    TRAITS = [Trait.INTERNET]

    def __init__(self, *args, **kwargs):
        """Setup our frames map and custom QNetworkAccessManager."""

        frames = self._frames = {}

        class InterceptingNAM(QNetworkAccessManager):
            def createRequest(self, op, req, *args, **kwargs):
                frame = req.originatingObject()

                if frame in frames and '/translate_tts' in req.url().toString():
                    callbacks = frames[frame]
                    rep = QNetworkAccessManager.createRequest(self, op, req,
                                                              *args, **kwargs)

                    def finished():
                        if rep.error():
                            callbacks['fail']("error in network reply")
                        elif rep.header(HEADER_LOCATION):
                            callbacks['fail']("got redirected away")
                        elif rep.header(HEADER_CONTENT_TYPE) != 'audio/mpeg':
                            callbacks['fail']("unexpected Content-Type")
                        elif rep.header(HEADER_CONTENT_LENGTH) < 1024:
                            callbacks['fail']("Content-Length is too small")
                        else:
                            stream = rep.readAll()
                            if not stream:
                                callbacks['fail']("no stream returned")
                            elif len(stream) < 1024:
                                callbacks['fail']("stream is too small")
                            else:
                                callbacks['okay'](stream)

                    rep.finished.connect(finished)

                return QNetworkAccessManager.createRequest(self, op, req,
                                                           *args, **kwargs)

        self._nam = InterceptingNAM()

        super(Google, self).__init__(*args, **kwargs)

    def desc(self):
        """Returns voice count and character count limit."""

        return ("Google Translate text-to-speech web API (%d voices; "
                "limited to %d characters of input)") % (len(VOICES), LIMIT)

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

        self._netops += 30

        page = QWebPage()
        page.setNetworkAccessManager(self._nam)

        frame = page.mainFrame()
        frames = self._frames
        def okay(stream):
            if frame in frames:
                del frames[frame]
                router_success(stream)
        def fail(message):
            if frame in frames:
                del frames[frame]
                router_error(SocketError(message))
        frames[frame] = dict(okay=okay, fail=fail, page=page)

        def load_finished(successful):
            if successful:
                frame.evaluateJavaScript(SCRIPT)
            else:
                fail("Cannot load Google Translate page")
        frame.loadFinished.connect(load_finished)

        url = QUrl('https://translate.google.com/')
        url.addQueryItem('sl', options['voice'])
        url.addQueryItem('q', text)
        frame.load(url)

        def timeout():
            fail("Request timed out")
        QTimer.singleShot(10000, timeout)

    def run(self, text, options, path):
        """Grab the stream from our prerun and write it to disk."""

        with open(path, 'wb') as output:
            output.write(options['prerun'])
        self.util_pad(path)

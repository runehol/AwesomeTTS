# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2014       Dave Shifflett
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
Service implementation for OS X's say command
"""

__all__ = ['TTS_service']

from os import unlink
import re
from subprocess import check_output, Popen
from PyQt4 import QtGui
from anki.utils import isMac, stripHTML
from awesometts import conf
from awesometts.paths import media_filename
from awesometts.util import TO_TOKENS


BINARY = 'say'
VOICES = None

if isMac:
    # n.b. voices *can* have spaces; optionally also capture language code
    RE_VOICE = re.compile(r'^\s*([-\w]+( [-\w]+)*)(\s+([-\w]+))?')

    try:
        VOICES = sorted([
            (
                # voice name
                match.group(1),

                # dropdown description
                "%s (%s)" % (match.group(1), match.group(4).replace('_', '-'))
                if match.group(4)
                else match.group(1),
            )
            for match
            in [
                RE_VOICE.match(line)
                for line
                in check_output([BINARY, '-v', '?']).split('\n')
            ]
            if match
        ], key=lambda voice: str.lower(voice[0]))

        if not VOICES:
            raise EnvironmentError("No usable output from call to `say -v ?`")

    except:  # allow recovery from any exception, pylint:disable=W0702
        from sys import stderr
        from traceback import format_exc

        stderr.write(
            "Although you are running OS X, the voice list from the `say` "
            "utility could not be retrieved. Any cards using `say` will not "
            "be speakable during this session. If this persists, please open "
            "an issue at <https://github.com/AwesomeTTS/AwesomeTTS/issues>.\n"
            "\n" +
            format_exc()
        )


if VOICES:
    SERVICE = 'say'

    def play(text, voice):
        text = re.sub(
            r'\[sound:.*?\]',
            '',
            stripHTML(text.replace('\n', '')).encode('utf-8'),
        )

        Popen([BINARY, '-v', voice, text]).wait()

    def record(text, voice):
        text = re.sub(
            r'\[sound:.*?\]',
            '',
            stripHTML(text.replace('\n', '')).encode('utf-8'),
        )

        filename_aiff = media_filename(text, SERVICE, voice, 'aiff')
        filename_mp3 = media_filename(text, SERVICE, voice, 'mp3')

        Popen([BINARY, '-v', voice, '-o', filename_aiff, text]).wait()

        Popen(
            ['lame'] +
            TO_TOKENS(conf.lame_flags) +
            [filename_aiff, filename_mp3],
        ).wait()

        unlink(filename_aiff)

        return filename_mp3

    def fg_layout(form):
        form.comboBoxSay = QtGui.QComboBox()
        form.comboBoxSay.addItems([voice[1] for voice in VOICES])
        form.comboBoxSay.setCurrentIndex(fg_layout.default_voice)

        text_label = QtGui.QLabel()
        text_label.setText("Voice:")

        vertical_layout = QtGui.QVBoxLayout()
        vertical_layout.addWidget(text_label)
        vertical_layout.addWidget(form.comboBoxSay)

        return vertical_layout

    def fg_preview(form):
        return play(
            unicode(form.texttoTTS.toPlainText()),
            VOICES[form.comboBoxSay.currentIndex()][0]
        )


    fg_layout.default_voice = 0

    TTS_service = {SERVICE: {
        'name': "OS X Say",
        'play': play,
        'record': record,
        'voices': VOICES,
        'filegenerator_layout': fg_layout,
        'filegenerator_preview': fg_preview,
    }}

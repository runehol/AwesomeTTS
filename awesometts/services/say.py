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

import re
from subprocess import check_output, Popen, PIPE, STDOUT
from PyQt4 import QtGui
from anki.utils import isMac, stripHTML
from awesometts.util import generateFileName


if isMac:
    SERVICE = 'say'

    VOICES = check_output("say -v ? |sed 's/  .*//'", shell=True)
    VOICES = VOICES.split('\n')
    VOICES.pop()

    def play(text, voice):
        text = re.sub(
            r'\[sound:.*?\]',
            '',
            stripHTML(text.replace('\n', '')).encode('utf-8'),
        )

        Popen(
            ['say', '-v', voice, text],
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
        ).communicate()

    def play_html(fromtag):
        for item in fromtag:
            text = ''.join(item.findAll(text=True))
            voice = item['voice']
            play(text, voice)

    def play_tag(fromtag):
        for item in fromtag:
            match = re.match(r'(.*?):(.*)', item, re.M|re.I)
            play(match.group(2), match.group(1))

    def record(form, text):
        fg_layout.default_voice = form.comboBoxSay.currentIndex()

        text = re.sub(
            r'\[sound:.*?\]',
            '',
            stripHTML(text.replace('\n', '')).encode('utf-8'),
        )
        voice = VOICES[form.comboBoxSay.currentIndex()]

        filename_aiff = generateFileName(text, SERVICE, 'iso-8859-1', '.aiff')
        filename_mp3 = generateFileName(text, SERVICE, 'iso-8859-1', '.mp3')

        Popen(
            ['say', '-v', voice, '-o', filename_aiff, text],
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
        ).wait()

        Popen(
            ['lame', '--quiet', filename_aiff, filename_mp3],
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
        ).wait()

        Popen(
            ['rm', filename_aiff],
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
        ).wait()

        return filename_mp3.decode('utf-8')

    def fg_layout(form):
        form.comboBoxSay = QtGui.QComboBox()
        form.comboBoxSay.addItems(VOICES)
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
            VOICES[form.comboBoxSay.currentIndex()]
        )

    def fg_run(form):
        return record(form, unicode(form.texttoTTS.toPlainText()))

    fg_layout.default_voice = 0

    TTS_service = {SERVICE: {
        'name': "OS X Say",
        'play': play,
        'playfromHTMLtag': play_html,
        'playfromtag': play_tag,
        'record': record,
        'filegenerator_layout': fg_layout,
        'filegenerator_preview': fg_preview,
        'filegenerator_run': fg_run,
    }}

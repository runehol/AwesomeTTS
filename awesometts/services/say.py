# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2012  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
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


from PyQt4 import QtGui,QtCore
import re, subprocess
from anki.utils import stripHTML, isMac
from urllib import quote_plus
import awesometts.config as config
import awesometts.util as util
from subprocess import Popen, PIPE, STDOUT

if isMac:

	vlist = subprocess.check_output("say -v ? |sed 's/  .*//'", shell=True)

	voicelist = vlist.split('\n')
	voicelist.pop()

	def playOSXsayTTS(text, voice):
		text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
		subprocess.Popen(['say', '-v', voice, text], stdin=PIPE, stdout=PIPE, stderr=STDOUT).communicate()


	def playfromtagOSXsayTTS(fromtag):
		print fromtag
		for item in fromtag:
			match = re.match("(.*?):(.*)", item, re.M|re.I)
			playOSXsayTTS(match.group(2), match.group(1))

	def playfromHTMLtagOSXsayTTS(fromtag):
		for item in fromtag:
			text = text = ''.join(item.findAll(text=True))
			voice = item['voice']
			playOSXsayTTS(text, voice)

	def recordOSXsayTTS(text, voice):
		text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
		filename_aiff = util.generateFileName(text, 'say', 'iso-8859-1', '.aiff')
		filename_mp3 = util.generateFileName(text, 'say', 'iso-8859-1', '.mp3')
		subprocess.Popen(['say', '-v', voice, '-o', filename_aiff, text], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
		subprocess.Popen(['lame', '--quiet', filename_aiff, filename_mp3], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
		subprocess.Popen(['rm', filename_aiff], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
		return filename_mp3.decode('utf-8')

	def filegenerator_layout(form):
		global DefaultSayVoice
		verticalLayout = QtGui.QVBoxLayout()
		textEditlabel = QtGui.QLabel()
		textEditlabel.setText("Voice:")
		form.comboBoxSay = QtGui.QComboBox()
		form.comboBoxSay.addItems(voicelist)
		form.comboBoxSay.setCurrentIndex(DefaultSayVoice) # get Default

		verticalLayout.addWidget(textEditlabel)
		verticalLayout.addWidget(form.comboBoxSay)
		return verticalLayout

	def recordOSXsayTTS_form(form, text):
		global DefaultSayVoice
		DefaultSayVoice = form.comboBoxSay.currentIndex() #set new Default
		return recordOSXsayTTS(text, voicelist[form.comboBoxSay.currentIndex()])

	def filegenerator_run(form):
		global DefaultSayVoice
		DefaultSayVoice = form.comboBoxSay.currentIndex() #set new Default
		return recordOSXsayTTS(unicode(form.texttoTTS.toPlainText()), voicelist[form.comboBoxSay.currentIndex()])

	def filegenerator_preview(form):
		return playOSXsayTTS(unicode(form.texttoTTS.toPlainText()), voicelist[form.comboBoxSay.currentIndex()])
	
	DefaultSayVoice = 0

	TTS_service = {'say' : {
	'name': 'OSX Say',
	'play' : playOSXsayTTS,
	'playfromtag' : playfromtagOSXsayTTS,
	'playfromHTMLtag' : playfromHTMLtagOSXsayTTS,
	'record' : recordOSXsayTTS_form,
	'filegenerator_layout': filegenerator_layout,
	'filegenerator_preview': filegenerator_preview,
	'filegenerator_run': filegenerator_run}}



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

from PyQt4 import QtGui,QtCore

from awesometts.paths import CACHE_DIR, relative

#Supported Languages       
# code , Language, windows charset encoding
slanguages = [['af', 'Afrikaans', 'cp1252'], #or iso-8859-1
['sq', 'Albanian',	'cp1250'], #or iso 8859-16
['ar', 'Arabic',	'cp1256'], #or iso-8859-6
['hy', 'Armenian',	'armscii-8'],
['bs', 'Bosnian',	'cp1250'], #or iso-8859-2
['ca', 'Catalan',	'cp1252'], #or iso-8859-1
['zh', 'Chinese',	'cp936'],
['hr', 'Croatian',	'cp1250'], #or iso-8859-2
['cs', 'Czech',		'cp1250'], #or iso-8859-2
['da', 'Danish',	'cp1252'], #or iso-8859-1
['nl', 'Dutch',		'cp1252'], #or iso-8859-1
['en', 'English',	'cp1252'], #or iso-8859-1
['eo', 'Esperanto',	'cp28593'], #or iso-8859-3
['fi', 'Finnish',	'cp1252'], #or iso-8859-1
['fr', 'French',	'cp1252'], #or iso-8859-1
['de', 'German',	'cp1252'], #or iso-8859-1
['el', 'Greek',		'cp1253'], #or iso-8859-7
['ht', 'Haitian Creole','cp1252'], #or iso-8859-1
['hi', 'Hindi',		'cp1252'], #or iso-8859-1
['hu', 'Hungarian',	'cp1250'], #or iso-8859-2
['is', 'Icelandic',	'cp1252'], #or iso-8859-1
['id', 'Indonesian'],
['it', 'Italian',	'cp1252'], #or iso-8859-1
['ja', 'Japanese',	'cp932'], #or shift_jis, iso-2022-jp, euc-jp
['ko', 'Korean',	'cp949'], #or euc-kr
['la', 'Latin'],
['lv', 'Latvian',	'cp1257'], #or iso-8859-13
['mk', 'Macedonian',	'cp1251'], #iso-8859-5
['no', 'Norwegian',	'cp1252'], #or iso-8859-1
['pl', 'Polish',	'cp1250'], #or iso-8859-2
['pt', 'Portuguese',	'cp1252'], #or iso-8859-1
['ro', 'Romanian',	'cp1250'], #or iso-8859-2
['ru', 'Russian',	'cp1251'], #or koi8-r, iso-8859-5
['sr', 'Serbian',	'cp1250'], # cp1250 for latin, cp1251 for cyrillic
['sk', 'Slovak',	'cp1250'], #or iso-8859-2
['es', 'Spanish',	'cp1252'], #or iso-8859-1
['sw', 'Swahili',	'cp1252'], #or iso-8859-1
['sv', 'Swedish',	'cp1252'], #or iso-8859-1
['ta', 'Tamil',		'cp57004'], #or x-iscii-ta
['th', 'Thai',		'cp874'], #or iso-8859-11
['tr', 'Turkish',	'cp1254'], #or iso-8859-9
['vi', 'Vietnamese',	'cp1258'],
['cy', 'Welsh',		'iso-8859-14']]



TTS_ADDRESS = 'http://translate.google.com/translate_tts'


import re, subprocess, urllib
from anki.utils import stripHTML
from urllib import quote_plus
import awesometts.config as config
from subprocess import Popen, PIPE, STDOUT
from awesometts.paths import media_filename
from awesometts.util import STARTUP_INFO



# Prepend http proxy if one is being used.  Scans the environment for
# a variable named "http_proxy" for all operating systems
# proxy code contributted by Scott Otterson
proxies = urllib.getproxies()

if len(proxies)>0 and "http" in proxies:
	proxStr = re.sub("http:", "http_proxy:", proxies['http'])
	TTS_ADDRESS = proxStr + "/" + TTS_ADDRESS



def get_language_id(language_code):
	x = 0
	for d in slanguages:
		if d[0]==language_code:
			return x
		x = x + 1


class PlayGoogleTTSDownloader:
	hadNetworkError = False
	hadResponseError = False
	threads = { }

	@staticmethod
	def fetch(address, cacheToken, cachePathname):
		for key in PlayGoogleTTSDownloader.threads.keys():
			if PlayGoogleTTSDownloader.threads[key].isFinished():
				del PlayGoogleTTSDownloader.threads[key]

		if not cacheToken in PlayGoogleTTSDownloader.threads:
			PlayGoogleTTSDownloader.threads[cacheToken] = PlayGoogleTTSWorker(
				address,
				cachePathname
			)
			PlayGoogleTTSDownloader.threads[cacheToken].start()

class PlayGoogleTTSWorker(QtCore.QThread):
	def __init__(self, address, cachePathname):
		QtCore.QThread.__init__(self)
		self.address = address
		self.cachePathname = cachePathname

	def run(self):
		import sys
		import urllib2

		try:
			response = urllib2.urlopen(
				urllib2.Request(
					self.address,
					headers = { "User-Agent": "Mozilla/5.0" }
				),
				timeout = 15
			)

			if (
				response.getcode() == 200 and
				response.info().gettype() == 'audio/mpeg'
			):
				cacheOutput = open(self.cachePathname, 'wb')
				cacheOutput.write(response.read())
				cacheOutput.close()
				response.close()

				playGoogleTTS_mplayer(self.cachePathname)

			else:
				if not PlayGoogleTTSDownloader.hadResponseError:
					sys.stderr.write('\n'.join([
						'Google TTS did not return an MP3.',
						self.address,
						'',
						'Report this error if it persists. '
						'This will only be displayed once this session.',
						''
					]))
					PlayGoogleTTSDownloader.hadResponseError = True

		except Exception, exception:
			if not PlayGoogleTTSDownloader.hadNetworkError:
				type, value, tb = sys.exc_info()
				sys.stderr.write('\n'.join([
					'The download from Google TTS failed.',
					self.address,
					'',
					str(exception),
					'',
					'Check your network connectivity, '
					'or report this error if it persists. '
					'This will only be displayed once this session.',
					''
				]))
				PlayGoogleTTSDownloader.hadNetworkError = True

def playGoogleTTS(text, language):
	text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
	text = re.sub("^\s+|\s+$", "", re.sub("\s+", " ", text))

	address = TTS_ADDRESS+'?tl='+language+'&q='+ quote_plus(text)

	if config.get('caching'):
		import hashlib
		import os

		if not os.path.isdir(CACHE_DIR):
			os.mkdir(CACHE_DIR)

		cacheFilename = media_filename(text, 'g', language, 'mp3')
		cachePathname = relative(CACHE_DIR, cacheFilename)

		if os.path.isfile(cachePathname):
			playGoogleTTS_mplayer(cachePathname)

		else:
			PlayGoogleTTSDownloader.fetch(
				address,
				cacheFilename,
				cachePathname
			)

	else:
		playGoogleTTS_mplayer(address)

def playGoogleTTS_mplayer(address):
	if subprocess.mswindows:
		param = ['mplayer.exe', '-ao', 'win32', '-slave', '-user-agent', "'Mozilla/5.0'", address]
		if config.get('subprocessing'):
			subprocess.Popen(param, startupinfo=STARTUP_INFO, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
		else:
			subprocess.Popen(param, startupinfo=STARTUP_INFO, stdin=PIPE, stdout=PIPE, stderr=STDOUT).communicate()
	else:
		param = ['mplayer', '-slave', '-user-agent', "'Mozilla/5.0'", address]
		if config.get('subprocessing'):
			subprocess.Popen(param, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
		else:
			subprocess.Popen(param, stdin=PIPE, stdout=PIPE, stderr=STDOUT).communicate()

def playfromtagGoogleTTS(fromtag):
	for item in fromtag:
		match = re.match("(.*?):(.*)", item, re.M|re.I)
		playGoogleTTS(match.group(2), match.group(1))

def playfromHTMLtagGoogleTTS(fromtag):
	for item in fromtag:
		text = ''.join(item.findAll(text=True))
		voice = item['voice']
		playGoogleTTS(text, voice)

def recordGoogleTTS(form, text):
	global DefaultGoogleVoice
	DefaultGoogleVoice = form.comboBoxGoogle.currentIndex() #set new Default
	return TTS_record_old(text, slanguages[form.comboBoxGoogle.currentIndex()][0])


def TTS_record_old(text, language):
	text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
	address = TTS_ADDRESS+'?tl='+language+'&q='+ quote_plus(text)
	
	file = media_filename(text, 'g', language, 'mp3')
	if subprocess.mswindows:
		subprocess.Popen(['mplayer.exe', '-ao', 'win32', '-slave', '-user-agent', "'Mozilla/5.0'", address, '-dumpstream', '-dumpfile', file], startupinfo=STARTUP_INFO, stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
	else:
		subprocess.Popen(['mplayer', '-slave', '-user-agent', "'Mozilla/5.0'", address, '-dumpstream', '-dumpfile', file], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
	return file.decode('utf-8')

def filegenerator_layout(form):
	global DefaultGoogleVoice
	verticalLayout = QtGui.QVBoxLayout()
	textEditlabel = QtGui.QLabel()
	textEditlabel.setText("Language:")

	font = QtGui.QFont()
       	font.setFamily("Monospace")
	form.comboBoxGoogle = QtGui.QComboBox()
	form.comboBoxGoogle.setFont(font)
	form.comboBoxGoogle.addItems([d[0] +' - '+ d[1] for d in slanguages])
	form.comboBoxGoogle.setCurrentIndex(DefaultGoogleVoice) # get Default

	verticalLayout.addWidget(textEditlabel)
	verticalLayout.addWidget(form.comboBoxGoogle)
	return verticalLayout

def filegenerator_run(form):
	global DefaultGoogleVoice
	DefaultGoogleVoice = form.comboBoxGoogle.currentIndex() #set new Default
	return TTS_record_old(unicode(form.texttoTTS.toPlainText()), slanguages[form.comboBoxGoogle.currentIndex()][0])

def filegenerator_preview(form):
	return playGoogleTTS(unicode(form.texttoTTS.toPlainText()), slanguages[form.comboBoxGoogle.currentIndex()][0])

DefaultGoogleVoice = get_language_id('en')

TTS_service = {'g' : {
'name': 'Google',
'play' : playGoogleTTS,
'playfromtag' : playfromtagGoogleTTS,
'playfromHTMLtag' : playfromHTMLtagGoogleTTS,
'record' : recordGoogleTTS,
'filegenerator_layout': filegenerator_layout,
'filegenerator_preview': filegenerator_preview,
'filegenerator_run': filegenerator_run}}




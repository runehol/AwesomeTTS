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


import os, sys, re, subprocess
from anki.utils import stripHTML
from urllib import quote_plus
import awesometts.config as config

file_max_length = 255 # Max filename length for Unix

def generateFileName(text, service, winencode='iso-8859-1', extention=".mp3"):
	if config.get('quote_mp3'): #re.sub removes \/:*?"<>|[]. from the file name
		file = quote_plus(re.sub('[\\\/\:\*\?"<>|\[\]\.]*', "",text)).replace("%", "")+extention
		if len(file) > file_max_length:
			file = file[0:file_max_length-len(extention)] + extention
	else:
		file = re.sub('[\\\/\:\*\?"<>|\[\]\.]*', "",text)+ extention
		if len(file) > file_max_length:
			file = file[0:file_max_length-len(extention)] + extention
		if subprocess.mswindows:
			file = file.decode('utf-8').encode(slanguages[get_language_id(language)][2])
	return file

# mplayer for MS Windows
if subprocess.mswindows:
	file_max_length = 100 #guess of a filename max length for Windows (filename +path = 255)
	dir = os.path.dirname(os.path.abspath(sys.argv[0]))
	os.environ['PATH'] += ";" + dir
	si = subprocess.STARTUPINFO()
	try:
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	except:
		# python2.7+
		si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
else:
	si = None #for plataforms other than MS Windows
	
def dumpUnicodeStr(src):
	return ''.join(["%04X" % ord(x) for x in src])

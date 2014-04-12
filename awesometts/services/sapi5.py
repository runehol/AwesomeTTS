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
Service implementation for SAPI 5 on the Windows platform
"""

__all__ = ['TTS_service']

from os import environ, unlink
from os.path import exists
from subprocess import mswindows, check_output, Popen
from awesometts import conf
from awesometts.paths import SERVICES_DIR, media_filename, relative
from awesometts.util import STARTUP_INFO, TO_HEXSTR, TO_TOKENS


VOICES = None

if mswindows:
    ROOT = environ.get('SYSTEMROOT', r'C:\Windows')

    BINARY = next(
        (
            fullpath
            for subdirectory in ['syswow64', 'system32']
            for filename in ['cscript.exe']
            for fullpath in [relative(ROOT, subdirectory, filename)]
            if exists(fullpath)
        ),
        None,
    )

    SCRIPT = relative(SERVICES_DIR, 'sapi5.vbs')

    if BINARY:
        try:
            VOICES = check_output(
                [BINARY, SCRIPT, '-vl'],
                startupinfo=STARTUP_INFO,
            ).split('\n')

            VOICES = sorted({
                (voice.strip(), voice.strip())
                for voice in VOICES[VOICES.index('--Voice List--') + 1:]
                if voice.strip()
            }, key=lambda voice: voice[1].lower())

        except:  # allow recovery from any exception, pylint:disable=W0702
            from sys import stderr
            from traceback import format_exc

            stderr.write(
                "Although you appear to have SAPI 5 support, the voice list "
                "from the VBS script not be retrieved. Any cards using SAPI "
                "may not be speakable during this session. If this persists, "
                "please open an issue at "
                "<https://github.com/AwesomeTTS/AwesomeTTS/issues>.\n"
                "\n" +
                format_exc()
            )


if VOICES:
    SERVICE = 'sapi5'

    def play(text, voice):
        param = [
            BINARY, SCRIPT, '-hex',
            '-voice', TO_HEXSTR(voice),
            TO_HEXSTR(text),
        ]

        if conf.subprocessing:
            Popen(param, startupinfo=STARTUP_INFO)
        else:
            Popen(param, startupinfo=STARTUP_INFO).wait()

    def record(text, voice):
        filename_wav = media_filename(text, SERVICE, voice, 'wav')
        filename_mp3 = media_filename(text, SERVICE, voice, 'mp3')

        Popen(
            [
                BINARY, SCRIPT, '-hex',
                '-o', filename_wav,
                '-voice', TO_HEXSTR(voice),
                TO_HEXSTR(text),
            ],
            startupinfo=STARTUP_INFO,
        ).wait()

        Popen(
            ['lame.exe'] +
            TO_TOKENS(conf.lame_flags) +
            [filename_wav, filename_mp3],
            startupinfo=STARTUP_INFO,
        ).wait()

        unlink(filename_wav)

        return filename_mp3


    TTS_service = {SERVICE: {
        'name': "SAPI 5",
        'play': play,
        'record': record,
        'voices': VOICES,
    }}

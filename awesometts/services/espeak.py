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
Service implementation for eSpeak voice engine
"""

__all__ = ['TTS_service']

from os import unlink
import re
from subprocess import check_output, mswindows, Popen
from awesometts import conf
from awesometts.paths import temp_path
from awesometts.util import STARTUP_INFO, TO_TOKENS


BINARY = 'espeak'
VOICES = None

RE_VOICE = re.compile(r'^\s*(\d+\s+)?([-\w]+)(\s+[-\w]\s+([-\w]+))?')

def _get_voices():
    voices = sorted([
        (
            # voice name
            match.group(2),

            # dropdown description
            "%s (%s)" % (match.group(4), match.group(2))
            if match.group(4)
            else match.group(2),
        )
        for match
        in [
            RE_VOICE.match(line)
            for line
            in check_output(
                [BINARY, '--voices'],
                startupinfo=STARTUP_INFO,
            ).split('\n')
        ]
        if match and match.group(2) != 'Pty'
    ], key=lambda voice: str.lower(voice[1]))

    if not voices:
        raise EnvironmentError("No usable output from `espeak --voices`")

    return voices

try:
    try:
        VOICES = _get_voices()

    except OSError as os_error:
        from errno import ENOENT

        if os_error.errno == ENOENT:
            if mswindows:
                import _winreg as winreg  # for Windows, pylint: disable=F0401

                try:
                    with winreg.ConnectRegistry(
                        None,  # use registry on local machine
                        winreg.HKEY_LOCAL_MACHINE
                    ) as hkey_hklm:
                        with winreg.OpenKey(
                            hkey_hklm,
                            r'Software\Microsoft\Speech\Voices\Tokens\eSpeak',
                        ) as hkey_espeak:
                            BINARY = r'%s\command_line\%s.exe' % (
                                winreg.QueryValueEx(hkey_espeak, 'Path')[0],
                                BINARY,
                            )

                            VOICES = _get_voices()

                except OSError as os_error:
                    if os_error.errno != ENOENT:
                        raise os_error

        else:
            raise os_error

except:  # allow recovery from any exception, pylint:disable=W0702
    from sys import stderr
    from traceback import format_exc

    stderr.write(
        "Although you appear to have eSpeak, the voice list from the CLI "
        "utility could not be retrieved. Any cards using `espeak` will not "
        "be speakable during this session. If this persists, please open "
        "an issue at <https://github.com/AwesomeTTS/AwesomeTTS/issues>.\n"
        "\n" +
        format_exc()
    )


if VOICES:
    SERVICE = 'espeak'

    def _file_workaround(text, voice):
        """
        If running on Windows and the given text cannot be represented
        purely with ASCII characters, returns a path to a temporary
        text file that may be used to feed eSpeak.

        Returns False otherwise.
        """

        if mswindows:
            try:
                text.encode('ascii')
            except UnicodeError:
                from codecs import open as copen

                path_txt = temp_path(text, SERVICE, voice, 'txt')

                with copen(path_txt, mode='w', encoding='utf-8') as out:
                    out.write(text)

                return path_txt

        return False

    def play(text, voice):
        path_txt = _file_workaround(text, voice)

        if path_txt:
            Popen(
                [BINARY, '-v', voice, '-f', path_txt],
                startupinfo=STARTUP_INFO,
            ).wait()

            unlink(path_txt)

        else:
            Popen(
                [BINARY, '-v', voice, text],
                startupinfo=STARTUP_INFO,
            ).wait()

    def record(text, voice):
        path_wav = temp_path(text, SERVICE, voice, 'wav')
        path_mp3 = temp_path(text, SERVICE, voice, 'mp3')
        path_txt = _file_workaround(text, voice)

        if path_txt:
            Popen(
                [BINARY, '-v', voice, '-w', path_wav, '-f', path_txt],
                startupinfo=STARTUP_INFO,
            ).wait()

            unlink(path_txt)

        else:
            Popen(
                [BINARY, '-v', voice, '-w', path_wav, text],
                startupinfo=STARTUP_INFO,
            ).wait()

        Popen(
            ['lame'] +
            TO_TOKENS(conf.lame_flags) +
            [path_wav, path_mp3],
            startupinfo=STARTUP_INFO,
        ).wait()

        unlink(path_wav)

        return path_mp3


    TTS_service = {SERVICE: {
        'name': "eSpeak",
        'play': play,
        'record': record,
        'voices': VOICES,
    }}

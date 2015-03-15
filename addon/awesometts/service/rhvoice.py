# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2015       Anki AwesomeTTS Development Team
# Copyright (C) 2015       Dave Shifflett
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
Service implementation for RHVoice
"""

__all__ = ['RHVoice']

from .base import Service
from .common import Trait


VOICES_DIR = '/usr/share/RHVoice/voices'
INFO_FILE = 'voice.info'

NAME_KEY = 'name'
LANGUAGE_KEY = 'language'
GENDER_KEY = 'gender'

PERCENT_VALUES = (-100, +100, "%")
PERCENT_TRANSFORM = lambda i: min(max(-100, int(round(float(i)))), +100)
DECIMALIZE = lambda p: round(p / 100.0, 2)


class RHVoice(Service):
    """Provides a Service-compliant implementation for RHVoice."""

    __slots__ = [
        '_voice_list',    # sorted list of (voice value, human label) tuples
        '_backgrounded',  # True if AwesomeTTS needed to start the service
    ]

    NAME = "RHVoice"

    TRAITS = [Trait.TRANSCODING]

    def __init__(self, *args, **kwargs):
        """
        Searches the RHVoice voice path for usable voices and populates
        the voices list.
        """

        if not self.IS_LINUX:
            raise EnvironmentError("AwesomeTTS only knows how to work w/ the "
                                   "Linux version of RHVoice at this time.")

        super(RHVoice, self).__init__(*args, **kwargs)

        from os import listdir
        from os.path import join, isdir, isfile

        def get_voice_info(voice_file):
            """Given a voice.info path, return a dict of voice info."""
            try:
                lookup = {}
                with open(voice_file) as voice_info:
                    for line in voice_info:
                        tokens = line.split('=', 1)
                        lookup[tokens[0]] = tokens[1].strip()
                return lookup
            except StandardError:
                return {}

        self._voice_list = [
            (
                voice_name,
                "%s (%s, %s)" % (
                    voice_info.get(NAME_KEY, voice_name),
                    voice_info.get(LANGUAGE_KEY, "no language"),
                    voice_info.get(GENDER_KEY, "no gender"),
                ),
            )
            for voice_name, voice_info in sorted(
                (
                    (voice_name, get_voice_info(voice_file))
                    for (voice_name, voice_file) in (
                        (voice_name, voice_file)
                        for (voice_name, voice_file)
                        in (
                            (voice_name, join(voice_dir, INFO_FILE))
                            for (voice_name, voice_dir)
                            in (
                                (voice_name, join(VOICES_DIR, voice_name))
                                for voice_name in listdir(VOICES_DIR)
                            )
                            if isdir(voice_dir)
                        )
                        if isfile(voice_file)
                    )
                ),
                key=lambda (voice_name, voice_info): (
                    voice_info.get(LANGUAGE_KEY),
                    voice_info.get(NAME_KEY, voice_name),
                )
            )
        ]

        if not self._voice_list:
            raise EnvironmentError("No usable voices in %s" % VOICES_DIR)

        dbus_check = ''.join(self.cli_output_error('RHVoice-client',
                                                   '-s', '__awesometts_check'))
        if 'ServiceUnknown' in dbus_check and 'RHVoice' in dbus_check:
            self.cli_background('RHVoice-service')
            self._backgrounded = True
        else:
            self._backgrounded = False

    def desc(self):
        """Return short description with voice count."""

        return "RHVoice synthesizer (%d voices), %s" % (
            len(self._voice_list),
            "service started by AwesomeTTS" if self._backgrounded
            else "provided by host system"
        )

    def options(self):
        """Provides access to voice, speed, pitch, and volume."""

        voice_lookup = {self.normalize(voice[0]): voice[0]
                        for voice in self._voice_list}

        def transform_voice(value):
            """Normalize and attempt to convert to official voice."""
            normalized = self.normalize(value)
            return (voice_lookup[normalized] if normalized in voice_lookup
                    else value)

        return [
            dict(key='voice', label="Voice", values=self._voice_list,
                 transform=transform_voice),
            dict(key='speed', label="Speed", values=PERCENT_VALUES,
                 transform=PERCENT_TRANSFORM, default=0),
            dict(key='pitch', label="Pitch", values=PERCENT_VALUES,
                 transform=PERCENT_TRANSFORM, default=0),
            dict(key='volume', label="Volume", values=PERCENT_VALUES,
                 transform=PERCENT_TRANSFORM, default=0),
        ]

    def run(self, text, options, path):
        """
        Saves the incoming text into a file, and pipes it through
        RHVoice-client and back out to a temporary wave file. If
        successful, the temporary wave file will be transcoded to an MP3
        for consumption by AwesomeTTS.
        """

        try:
            input_txt = self.path_input(text)
            output_wav = self.path_temp('wav')

            self.cli_pipe(
                ['RHVoice-client',
                 '-s', options['voice'],
                 '-r', DECIMALIZE(options['speed']),
                 '-p', DECIMALIZE(options['pitch']),
                 '-v', DECIMALIZE(options['volume'])],
                input_path=input_txt,
                output_path=output_wav,
            )

            self.cli_transcode(output_wav,
                               path,
                               require=dict(size_in=4096))

        finally:
            self.path_unlink(input_txt, output_wav)

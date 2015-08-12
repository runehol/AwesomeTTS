# -*- coding: utf-8 -*-
# pylint:disable=bad-continuation

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2014-2015  Anki AwesomeTTS Development Team
# Copyright (C) 2014-2015  Dave Shifflett
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
Service classes for AwesomeTTS
"""

__all__ = [
    # common
    'Trait',

    # services
    'Baidu',
    'Ekho',
    'ESpeak',
    'Festival',
    'Google',
    'Howjsay',
    'ImTranslator',
    'Oxford',
    'Pico2Wave',
    'RHVoice',
    'SAPI5',
    'SAPI5JS',
    'Say',
    'SpanishDict',
    'TTSAPICom',
    'Yandex',
    'Youdao',
]

from .common import Trait

from .baidu import Baidu
from .ekho import Ekho
from .espeak import ESpeak
from .festival import Festival
from .google import Google
from .howjsay import Howjsay
from .imtranslator import ImTranslator
from .oxford import Oxford
from .pico2wave import Pico2Wave
from .rhvoice import RHVoice
from .sapi5 import SAPI5
from .sapi5js import SAPI5JS
from .say import Say
from .spanishdict import SpanishDict
from .ttsapicom import TTSAPICom
from .yandex import Yandex
from .youdao import Youdao

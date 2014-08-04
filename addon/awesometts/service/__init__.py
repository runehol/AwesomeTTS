# -*- coding: utf-8 -*-
# pylint:disable=bad-continuation

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2014       Anki AwesomeTTS Development Team
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
Service classes for AwesomeTTS
"""

__all__ = [
    # common
    'Trait',

    # services
    'Ekho',
    'ESpeak',
    'Festival',
    'Google',
    'Pico2Wave',
    'SAPI5',
    'Say',
    'TTSAPICom',
    'Yandex',
]

from .common import Trait

from .ekho import Ekho
from .espeak import ESpeak
from .festival import Festival
from .google import Google
from .pico2wave import Pico2Wave
from .sapi5 import SAPI5
from .say import Say
from .ttsapicom import TTSAPICom
from .yandex import Yandex

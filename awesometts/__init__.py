# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2013  Arthur Helfstein Fragoso
# Copyright (C) 2013-2014  Dave Shifflett
# Copyright (C) 2012       Dominic Lerbs
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
Add-on package initialization
"""

__all__ = []

import json
import logging
import os
import re
import sys

from PyQt4.QtCore import Qt

import anki
import aqt
import aqt.clayout

from . import (
    gui,
    service,
)

from .bundle import Bundle
from .config import Config
from .logger import Logger
from .router import Router


VERSION = "1.0 Beta 11"


# Paths
#
# n.b. When determining the code directory, abspath() is needed since
# the __file__ constant is not a full path by itself.

PATH_ADDON = os.path.dirname(os.path.abspath(__file__))

PATH_CACHE = os.path.join(PATH_ADDON, '.cache')
if not os.path.isdir(PATH_CACHE):
    os.mkdir(PATH_CACHE)

PATH_CONFIG = os.path.join(PATH_ADDON, 'config.db')

PATH_LOG = os.path.join(PATH_ADDON, 'addon.log')

PATH_TEMP = os.path.join(PATH_ADDON, '.temp')
if not os.path.isdir(PATH_TEMP):
    os.mkdir(PATH_TEMP)


# Regular expression patterns

RE_FILES = re.compile(r'[a-z\d]+(-[a-f\d]{8}){5}\.mp3')  # Router _path_cache

RE_WHITESPACE = re.compile(r'\s+')


# Conversions and transformations

TO_BOOL = lambda value: bool(int(value))  # workaround for bool('0') == True

TO_JSON_DICT = lambda value: isinstance(value, basestring) and \
    value.lstrip().startswith('{') and json.loads(value) or {}

TO_NORMALIZED = lambda value: ''.join(
    char.lower()
    for char in value
    if char.isalpha() or char.isdigit()
)


# Filters

STRIP_FILES = lambda text: RE_FILES.sub('', text).strip()

STRIP_HTML = anki.utils.stripHTML

STRIP_SOUNDS = anki.sound.stripSounds

STRIP_WHITESPACE = lambda text: RE_WHITESPACE.sub(' ', text).strip()

STRIP_ALL = lambda text: \
    STRIP_WHITESPACE(STRIP_FILES(STRIP_SOUNDS(STRIP_HTML(text))))


# Core class initialization and dependency setup, pylint:disable=C0103

logger = Logger(
    name='AwesomeTTS',
    handlers=dict(
        debug_file=logging.FileHandler(
            PATH_LOG,
            encoding='utf-8',
            delay=True,
        ),
        debug_stdout=logging.StreamHandler(sys.stdout),
    ),
    formatter=logging.Formatter(
        "[%(threadName)s %(asctime)s] %(pathname)s@%(lineno)d %(levelname)s\n"
        "%(message)s\n",
        "%H:%M:%S",
    ),
)

config = Config(
    db=Bundle(
        path=PATH_CONFIG,
        table='general',
        normalize=TO_NORMALIZED,
    ),
    cols=[
        ('automaticAnswers', 'integer', False, TO_BOOL, int),
        ('automaticQuestions', 'integer', False, TO_BOOL, int),
        ('debug_file', 'integer', False, TO_BOOL, int),
        ('debug_stdout', 'integer', False, TO_BOOL, int),
        ('lame_flags', 'text', '--quiet -q 2', str, str),
        ('last_mass_append', 'integer', True, TO_BOOL, int),
        ('last_mass_behavior', 'integer', True, TO_BOOL, int),
        ('last_mass_dest', 'text', 'Back', unicode, unicode),
        ('last_mass_source', 'text', 'Front', unicode, unicode),
        ('last_service', 'text', 'google', str, str),
        ('last_options', 'text', {}, TO_JSON_DICT, json.dumps),
        ('templater_field', 'text', 'Front', unicode, unicode),
        ('templater_hide', 'text', 'normal', str, str),
        ('templater_target', 'text', 'front', str, str),
        ('throttle_sleep', 'integer', 600, int, int),
        ('throttle_threshold', 'integer', 250, int, int),
        ('TTS_KEY_A', 'integer', Qt.Key_F4, Qt.Key, int),
        ('TTS_KEY_Q', 'integer', Qt.Key_F3, Qt.Key, int),
    ],
    logger=logger,
    events=[
        (
            ['debug_file', 'debug_stdout'],
            logger.activate,  # BufferedLogger instance, pylint: disable=E1103
        ),
    ],
)

router = Router(
    services=Bundle(
        mappings=[
            ('ekho', service.Ekho),
            ('espeak', service.ESpeak),
            ('festival', service.Festival),
            ('google', service.Google),
            ('sapi5', service.SAPI5),
            ('say', service.Say),
        ],
        aliases=[
            ('g', 'google'),
        ],
        normalize=TO_NORMALIZED,
        textize=STRIP_ALL,
        args=(),
        kwargs=dict(
            temp_dir=PATH_TEMP,
            lame_flags=lambda: config['lame_flags'],
            normalize=TO_NORMALIZED,
            logger=logger,
        ),
    ),
    cache_dir=PATH_CACHE,
    logger=logger,
)


# GUI interaction with Anki, pylint:disable=C0103
# n.b. be careful wrapping methods that have return values (see anki.hooks);
#      in general, only the 'before' mode absolves us of responsibility

addon = Bundle(
    config=config,
    logger=logger,
    paths=Bundle(
        cache=PATH_CACHE,
    ),
    router=router,
    strip=Bundle(
        sounds=STRIP_SOUNDS,
    ),
    version=VERSION,
)

reviewer = gui.Reviewer(
    addon=addon,
    playback=anki.sound.play,
    alerts=aqt.utils.showWarning,
    parent=aqt.mw,
)
anki.hooks.addHook(
    'showQuestion',
    lambda: reviewer.card_handler('question', aqt.mw.reviewer.card),
)
anki.hooks.addHook(
    'showAnswer',
    lambda: reviewer.card_handler('answer', aqt.mw.reviewer.card),
)
aqt.mw.reviewer._keyHandler = anki.hooks.wrap(
    aqt.mw.reviewer._keyHandler,
    lambda key_event, _old: reviewer.key_handler(
        key_event=key_event,
        state=aqt.mw.reviewer.state,
        card=aqt.mw.reviewer.card,
        propagate=_old,
    ),
    'around',  # setting 'around' allows me to block call to original function
)

gui.Action(
    target=Bundle(
        constructor=gui.Configurator,
        args=(),
        kwargs=dict(addon=addon, parent=aqt.mw),
    ),
    text="Awesome&TTS...",
    parent=aqt.mw.form.menuTools,
)

anki.hooks.addHook(
    'browser.setupMenus',
    lambda browser: gui.Action(
        target=Bundle(
            constructor=gui.BrowserGenerator,
            args=(),
            kwargs=dict(
                browser=browser,
                addon=addon,
                playback=anki.sound.play,
                alerts=aqt.utils.showWarning,
                parent=browser,
            ),
        ),
        text="Add Audio to Selected Notes w/ Awesome&TTS...",
        parent=browser.form.menuEdit,
    ),
)
aqt.browser.Browser.updateTitle = anki.hooks.wrap(
    aqt.browser.Browser.updateTitle,
    lambda browser: browser.findChild(gui.Action).setEnabled(
        bool(browser.form.tableView.selectionModel().selectedRows())
    ),
    'before',
)

anki.hooks.addHook(
    'setupEditorButtons',
    lambda editor: editor.iconsBox.addWidget(
        gui.Button(
            tooltip="Record and insert an audio clip here w/ AwesomeTTS",
            target=Bundle(
                constructor=gui.EditorGenerator,
                args=(),
                kwargs=dict(
                    editor=editor,
                    addon=addon,
                    playback=anki.sound.play,
                    alerts=aqt.utils.showWarning,
                    parent=editor.parentWindow,
                ),
            ),
            style=editor.plastiqueStyle,
        ),
    ),
)
aqt.editor.Editor.enableButtons = anki.hooks.wrap(
    aqt.editor.Editor.enableButtons,
    lambda editor, val=True: (
        editor.widget.findChild(gui.Button).setEnabled(val),

        # Temporarily disable shortcut to Browser window's "Add Audio to
        # Selected Notes" menu so this more "local" shortcut works instead.
        # Has no effect on "Add" as findChildren() returns empty list there.
        [action.muzzle(val) for action
            in editor.parentWindow.findChildren(gui.Action)],
    ),
    'before',
)

aqt.clayout.CardLayout.setupButtons = anki.hooks.wrap(
    aqt.clayout.CardLayout.setupButtons,
    lambda card_layout: card_layout.buttons.insertWidget(
        # today, the card layout form has 7 buttons/stretchers; in the event
        # that this changes in the future, bump the button to the first slot
        3 if card_layout.buttons.count() == 7 else 0,
        gui.Button(
            text="Add &TTS",
            tooltip="Insert a tag for on-the-fly playback w/ AwesomeTTS",
            target=Bundle(
                constructor=gui.Templater,
                args=(),
                kwargs=dict(
                    card_layout=card_layout,
                    addon=addon,
                    playback=anki.sound.play,
                    alerts=aqt.utils.showWarning,
                    parent=card_layout,
                ),
            ),
        ),
    ),
    'after',  # must use 'after' so that 'buttons' attribute is set
)

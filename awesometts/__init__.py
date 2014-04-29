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
import os.path
import re
import sys

from PyQt4.QtCore import Qt

import anki.hooks
import anki.utils
import anki.sound
import aqt
import aqt.clayout
import aqt.editor
import aqt.utils

from . import classes


VERSION = "1.0 Beta 11 (develop)"


# Paths
#
# n.b. When determining the code directory, abspath() is needed since
# the __file__ constant is not a full path by itself.

PATH_ADDON = os.path.dirname(os.path.abspath(__file__))

PATH_CACHE = os.path.join(PATH_ADDON, 'cache')
if not os.path.isdir(PATH_CACHE):
    os.mkdir(PATH_CACHE)

PATH_CONFIG = os.path.join(PATH_ADDON, 'config.db')

PATH_LOG = os.path.join(PATH_ADDON, 'addon.log')

PATH_TEMP = os.path.join(PATH_ADDON, 'temp')
if not os.path.isdir(PATH_TEMP):
    os.mkdir(PATH_TEMP)


# Regular expression patterns

RE_SOUND_BRACKET_TAG = re.compile(r'\[sound:[^\]]+\]', re.IGNORECASE)

RE_WHITESPACE = re.compile(r'\s+')


# Conversions and transformations

TO_BOOL = lambda value: bool(int(value))  # workaround for bool('0') == True

TO_NORMALIZED = lambda value: ''.join(
    char.lower()
    for char in value
    if char.isalpha() or char.isdigit()
)


# Filters

STRIP_HTML = anki.utils.stripHTML

STRIP_SOUNDS = lambda text: RE_SOUND_BRACKET_TAG.sub('', text).strip()

STRIP_WHITESPACE = lambda text: RE_WHITESPACE.sub(' ', text).strip()

STRIP_ALL = lambda text: STRIP_WHITESPACE(STRIP_SOUNDS(STRIP_HTML(text)))


# Core class initialization and dependency setup, pylint:disable=C0103

logger = classes.Logger(
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

config = classes.Config(
    db=classes.Bundle(
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
        ('last_mass_dest', 'text', 'Back', str, str),
        ('last_mass_source', 'text', 'Front', str, str),
        ('last_service', 'text', 'google', str, str),
        ('last_options', 'text', {}, json.loads, json.dumps),
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

router = classes.Router(
    services=classes.Bundle(
        mappings=[
            ('ekho', classes.services.Ekho),
            ('espeak', classes.services.ESpeak),
            ('google', classes.services.Google),
            ('sapi5', classes.services.SAPI5),
            ('say', classes.services.Say),
        ],
        aliases=[
            ('g', 'google'),
        ],
        normalize=TO_NORMALIZED,
        textize=STRIP_ALL,
        args=(),
        kwargs=dict(
            temp_dir=PATH_TEMP,
            lame_flags=config['lame_flags'],
            logger=logger,
        ),
    ),
    cache_dir=PATH_CACHE,
    logger=logger,
)


# GUI interaction with Anki, pylint:disable=C0103
# n.b. be careful wrapping methods that have return values; see anki.hooks

from .classes.gui.base import ServiceDialog  # FIXME remove

addon = classes.Bundle(
    config=config,
    logger=logger,
    paths=classes.Bundle(
        cache=PATH_CACHE,
    ),
    router=router,
    version=VERSION,
)

reviewer = classes.gui.Reviewer(
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

classes.gui.Action(
    target=classes.Bundle(
        constructor=classes.gui.Configurator,
        args=(),
        kwargs=dict(addon=addon, parent=aqt.mw),
    ),
    text="Awesome&TTS...",
    parent=aqt.mw.form.menuTools,
)

anki.hooks.addHook(
    # FIXME menu should gray when no cards are selected in Browser
    'browser.setupMenus',
    lambda browser: classes.gui.Action(
        target=classes.Bundle(
            constructor=classes.gui.BrowserGenerator,
            args=(),
            kwargs=dict(
                addon=addon,
                playback=anki.sound.play,
                alerts=aqt.utils.showWarning,
                parent=browser,
            ),
        ),
        text="Awesome&TTS Mass Generator...",
        parent=browser.form.menuEdit,
    ),
)

anki.hooks.addHook(
    'setupEditorButtons',
    lambda editor: editor.iconsBox.addWidget(
        classes.gui.Button(
            target=classes.Bundle(
                constructor=classes.gui.EditorGenerator,
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
    lambda editor, val=True: editor.widget.findChild(classes.gui.Button)
        .setEnabled(val),
    'before',
)

aqt.clayout.CardLayout.setupButtons = anki.hooks.wrap(
    aqt.clayout.CardLayout.setupButtons,
    lambda card_layout: card_layout.buttons.insertWidget(
        # today, the card layout form has 7 buttons/stretchers; in the event
        # that this changes in the future, bump the button to the first slot
        3 if card_layout.buttons.count() == 7 else 0,
        classes.gui.Button(
            text="Add &TTS",
            target=classes.Bundle(
                constructor=ServiceDialog,  # FIXME replace w/ TemplateBuilder
                args=(),
                kwargs=dict(
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

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

import inspect
import logging
import platform
import re
import sys
from time import time

from PyQt4.QtCore import PYQT_VERSION_STR, Qt, QEvent
from PyQt4.QtGui import QKeySequence

import anki
import aqt
import aqt.clayout

from . import conversion as to, gui, paths, service
from .bundle import Bundle
from .config import Config
from .logger import Logger
from .router import Router
from .updates import Updates


VERSION = '1.1.0-dev'

WEB = 'https://ankiatts.appspot.com'


# Core class initialization and dependency setup, pylint:disable=C0103

logger = Logger(
    name='AwesomeTTS',
    handlers=dict(
        debug_file=logging.FileHandler(
            paths.LOG,
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

sequences = {
    key: QKeySequence()
    for key in ['browser_generator', 'browser_stripper', 'configurator',
                'editor_generator', 'templater']
}

config = Config(
    db=Bundle(
        path=paths.CONFIG,
        table='general',
        normalize=to.NORMALIZED,
    ),
    cols=[
        ('automaticAnswers', 'integer', True, to.BOOL, int),
        ('automaticQuestions', 'integer', True, to.BOOL, int),
        ('debug_file', 'integer', False, to.BOOL, int),
        ('debug_stdout', 'integer', False, to.BOOL, int),
        ('delay_answers_onthefly', 'integer', 0, int, int),
        ('delay_answers_stored_ours', 'integer', 0, int, int),
        ('delay_answers_stored_theirs', 'integer', 0, int, int),
        ('delay_questions_onthefly', 'integer', 0, int, int),
        ('delay_questions_stored_ours', 'integer', 0, int, int),
        ('delay_questions_stored_theirs', 'integer', 0, int, int),
        ('lame_flags', 'text', '--quiet -q 2', str, str),
        ('last_mass_append', 'integer', True, to.BOOL, int),
        ('last_mass_behavior', 'integer', True, to.BOOL, int),
        ('last_mass_dest', 'text', 'Back', unicode, unicode),
        ('last_mass_source', 'text', 'Front', unicode, unicode),
        ('last_options', 'text', {}, to.JSON_DICT, to.compact_json),
        ('last_service', 'text', 'google', str, str),
        ('last_strip_mode', 'text', 'ours', str, str),
        ('launch_browser_generator', 'integer', Qt.ControlModifier | Qt.Key_T,
         to.NULLABLE_KEY, to.NULLABLE_INT),
        ('launch_browser_stripper', 'integer', None, to.NULLABLE_KEY,
         to.NULLABLE_INT),
        ('launch_configurator', 'integer', Qt.ControlModifier | Qt.Key_T,
         to.NULLABLE_KEY, to.NULLABLE_INT),
        ('launch_editor_generator', 'integer', Qt.ControlModifier | Qt.Key_T,
         to.NULLABLE_KEY, to.NULLABLE_INT),
        ('launch_templater', 'integer', Qt.ControlModifier | Qt.Key_T,
         to.NULLABLE_KEY, to.NULLABLE_INT),
        ('spec_note_count', 'text', '', unicode, unicode),
        ('spec_note_count_wrap', 'integer', True, to.BOOL, int),
        ('spec_note_ellipsize', 'text', '', unicode, unicode),
        ('spec_note_strip', 'text', '', unicode, unicode),
        ('spec_template_count', 'text', '', unicode, unicode),
        ('spec_template_count_wrap', 'integer', True, to.BOOL, int),
        ('spec_template_ellipsize', 'text', '', unicode, unicode),
        ('spec_template_strip', 'text', '', unicode, unicode),
        ('strip_note_braces', 'integer', False, to.BOOL, int),
        ('strip_note_brackets', 'integer', False, to.BOOL, int),
        ('strip_note_parens', 'integer', False, to.BOOL, int),
        ('strip_template_braces', 'integer', False, to.BOOL, int),
        ('strip_template_brackets', 'integer', False, to.BOOL, int),
        ('strip_template_parens', 'integer', False, to.BOOL, int),
        ('sub_note_cloze', 'text', 'anki', str, str),
        ('sub_template_cloze', 'text', 'anki', str, str),
        ('templater_cloze', 'integer', True, to.BOOL, int),
        ('templater_field', 'text', 'Front', unicode, unicode),
        ('templater_hide', 'text', 'normal', str, str),
        ('templater_target', 'text', 'front', str, str),
        ('throttle_sleep', 'integer', 30, int, int),
        ('throttle_threshold', 'integer', 10, int, int),
        ('TTS_KEY_A', 'integer', Qt.Key_F4, to.NULLABLE_KEY, to.NULLABLE_INT),
        ('TTS_KEY_Q', 'integer', Qt.Key_F3, to.NULLABLE_KEY, to.NULLABLE_INT),
        ('updates_enabled', 'integer', True, to.BOOL, int),
        ('updates_ignore', 'text', '', str, str),
        ('updates_postpone', 'integer', 0, int, lambda i: int(round(i))),
    ],
    logger=logger,
    events=[
        (
            ['debug_file', 'debug_stdout'],
            logger.activate,  # BufferedLogger instance, pylint: disable=E1103
        ),
        (
            ['launch_' + key for key in sequences.keys()],
            lambda config: ([sequences[key].swap(config['launch_' + key] or 0)
                            for key in sequences.keys()],
                            [conf_menu.setShortcut(sequences['configurator'])
                             for conf_menu in (aqt.mw.form.menuTools.
                                               findChildren(gui.Action))])
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
            ('pico2wave', service.Pico2Wave),
            ('sapi5', service.SAPI5),
            ('say', service.Say),
            ('spanishdict', service.SpanishDict),
            ('ttsapicom', service.TTSAPICom),
            ('yandex', service.Yandex),
        ],
        aliases=[
            ('g', 'google'),
        ],
        normalize=to.NORMALIZED,
        args=(),
        kwargs=dict(
            temp_dir=paths.TEMP,
            lame_flags=lambda: config['lame_flags'],
            normalize=to.NORMALIZED,
            logger=logger,
        ),
    ),
    cache_dir=paths.CACHE,
    logger=logger,
)

updates = Updates(
    agent='AwesomeTTS/%s (Anki %s; PyQt %s; %s %s; %s)' % (
        VERSION, anki.version, PYQT_VERSION_STR,
        platform.python_implementation(), platform.python_version(),
        platform.platform().replace('-', ' '),
    ),
    endpoint='%s/api/update/%s-%s' % (WEB, sys.platform, VERSION),
    logger=logger,
)


# GUI interaction with Anki, pylint:disable=C0103
# n.b. be careful wrapping methods that have return values (see anki.hooks);
#      in general, only the 'before' mode absolves us of responsibility

RE_CLOZE_NOTE = re.compile(anki.template.template.clozeReg % r'\d+')
RE_CLOZE_TEMPLATE = re.compile(
    # see anki.template.template.clozeText; n.b. the presence of the brackets
    # in the pattern means that this will only match and replace on the
    # question side of cards and that the answer side will be read normally
    r'<span class=.?cloze.?>\[(.+?)\]</span>'
)
RE_ELLIPSES = re.compile(r'\s*(\.\s*){3,}')
RE_FILENAMES = re.compile(r'[a-z\d]+(-[a-f\d]{8}){5}( \(\d+\))?\.mp3')
RE_SOUNDS = re.compile(r'\[sound:(.*?)\]')  # see also anki.sound._soundReg
RE_TEXT_IN_BRACES = re.compile(r'\{.+?\}')
RE_TEXT_IN_BRACKETS = re.compile(r'\[.+?\]')
RE_TEXT_IN_PARENS = re.compile(r'\(.+?\)')
RE_WHITESPACE = re.compile(r'[\0\s]+')

COLLAPSE_ELLIPSES = lambda text: RE_ELLIPSES.sub(' ... ', text)
COLLAPSE_WHITESPACE = lambda text: RE_WHITESPACE.sub(' ', text).strip()

SPEC_COUNT = lambda key, wrap_key, text: \
    re.sub(
        r'[' + re.escape(config[key]) + ']+',
        lambda match: str(len(match.group(0))).join(
            [' ... ', ' ... '] if config[wrap_key]
            else [' ', ' ']
        ),
        text,
    ) if config[key] \
    else text
SPEC_COUNT_NOTE = lambda text: SPEC_COUNT('spec_note_count',
                                          'spec_note_count_wrap',
                                          text)
SPEC_COUNT_TEMPLATE = lambda text: SPEC_COUNT('spec_template_count',
                                              'spec_template_count_wrap',
                                              text)

SPEC_STRIP = lambda key, text: \
    ''.join(c for c in text if c not in config[key]) if config[key] \
    else text
SPEC_STRIP_NOTE = lambda text: SPEC_STRIP('spec_note_strip', text)
SPEC_STRIP_TEMPLATE = lambda text: SPEC_STRIP('spec_template_strip', text)

SPEC_ELLIP = lambda key, text: \
    ''.join(('...' if c in config[key] else c) for c in text) if config[key] \
    else text
SPEC_ELLIP_NOTE = lambda text: SPEC_ELLIP('spec_note_ellipsize', text)
SPEC_ELLIP_TEMPLATE = lambda text: SPEC_ELLIP('spec_template_ellipsize', text)

STRIP_FILENAMES = lambda text: RE_FILENAMES.sub('', text)
STRIP_HTML = anki.utils.stripHTML  # this also converts character entities
STRIP_SOUNDS = lambda text, which=False: RE_SOUNDS.sub(
    (lambda match: match.group(0) if RE_FILENAMES.match(match.group(1))
     else '') if which == 'theirs'
    else (lambda match: '' if RE_FILENAMES.match(match.group(1))
          else match.group(0)) if which == 'ours'
    else '',

    text,
)

STRIP_CONDITIONALLY = lambda regex, key, text: \
    regex.sub('', text) if config[key] else text

STRIP_CONDITIONALLY_NOTE = lambda text: \
    STRIP_CONDITIONALLY(RE_TEXT_IN_BRACES, 'strip_note_braces',
    STRIP_CONDITIONALLY(RE_TEXT_IN_BRACKETS, 'strip_note_brackets',
    STRIP_CONDITIONALLY(RE_TEXT_IN_PARENS, 'strip_note_parens',
        text
    )))

STRIP_CONDITIONALLY_TEMPLATE = lambda text: \
    STRIP_CONDITIONALLY(RE_TEXT_IN_BRACES, 'strip_template_braces',
    STRIP_CONDITIONALLY(RE_TEXT_IN_BRACKETS, 'strip_template_brackets',
    STRIP_CONDITIONALLY(RE_TEXT_IN_PARENS, 'strip_template_parens',
        text
    )))

SUB_CLOZES_NOTE = lambda text: RE_CLOZE_NOTE.sub(
    lambda match:
        '...' if config['sub_note_cloze'] == 'ellipsize'
        else '' if config['sub_note_cloze'] == 'remove'
        else (
            '... %s ...' % match.group(3).strip('.') if
                match.group(3) and
                match.group(3).strip('.')
            else '...'
        ) if config['sub_note_cloze'] == 'wrap'
        else (
            match.group(1) if match.group(1)
            else '...'
        ) if config['sub_note_cloze'] == 'deleted'
        else match.group(3) if match.group(3)
        else '...',
    text,
)

SUB_CLOZES_TEMPLATE = lambda text: RE_CLOZE_TEMPLATE.sub(
    lambda match:
        '...' if config['sub_template_cloze'] == 'ellipsize'
        else '' if config['sub_template_cloze'] == 'remove'
        else '... %s ...' % match.group(1).strip('.') if
            config['sub_template_cloze'] == 'wrap' and
            match.group(1).strip('.')
        else match.group(1),
    text,
)


PLAY_ANKI = anki.sound.play

PLAY_BLANK = lambda seconds, reason, path: \
    logger.debug("Ignoring %d-second delay (%s): %s", seconds, reason, path) \
    if anki.sound.mplayerQueue \
    else (
        logger.debug("Need %d-second delay (%s): %s", seconds, reason, path),
        [PLAY_ANKI(paths.BLANK) for i in range(seconds)],
    )

PLAY_PREVIEW = lambda path: (
    PLAY_BLANK(0, "preview mode", path),
    PLAY_ANKI(path),
)

PLAY_ONTHEFLY_QUESTION = lambda path: (
    PLAY_BLANK(
        config['delay_questions_onthefly'],
        "on-the-fly automatic question",
        path,
    ),
    PLAY_ANKI(path),
)

PLAY_ONTHEFLY_ANSWER = lambda path: (
    PLAY_BLANK(
        config['delay_answers_onthefly'],
        "on-the-fly automatic answer",
        path,
    ),
    PLAY_ANKI(path),
)

PLAY_ONTHEFLY_SHORTCUT = lambda path: (
    PLAY_BLANK(0, "on-the-fly shortcut mode", path),
    PLAY_ANKI(path),
)

PLAY_WRAPPED = lambda path: (
    PLAY_BLANK(0, "wrapped, non-review", path) if aqt.mw.state != 'review'
    else PLAY_BLANK(0, "wrapped, blacklisted caller", path) if next(
        (
            True
            for frame in inspect.stack()
            if frame[3] in [
                'addMedia',     # if the user adds media in review
                'replayAudio',  # if the user strikes R or F5
            ]
        ),
        False,
    )
    else (
        PLAY_BLANK(
            config['delay_questions_stored_ours'],
            "wrapped, AwesomeTTS sound on question side",
            path,
        ) if RE_FILENAMES.search(path)
        else PLAY_BLANK(
            config['delay_questions_stored_theirs'],
            "wrapped, non-AwesomeTTS sound on question side",
            path,
        )
    ) if aqt.mw.reviewer.state == 'question'
    else (
        PLAY_BLANK(
            config['delay_answers_stored_ours'],
            "wrapped, AwesomeTTS sound on answer side",
            path,
        ) if RE_FILENAMES.search(path)
        else PLAY_BLANK(
            config['delay_answers_stored_theirs'],
            "wrapped, non-AwesomeTTS sound on answer side",
            path,
        )
    ) if aqt.mw.reviewer.state == 'answer'
    else PLAY_BLANK(0, "wrapped, unknown review state", path),

    PLAY_ANKI(path),
)

anki.sound.play = PLAY_WRAPPED


addon = Bundle(
    config=config,
    downloader=Bundle(
        base=aqt.addons.GetAddons,
        superbase=aqt.addons.GetAddons.__bases__[0],
        args=[aqt.mw],
        kwargs=dict(),
        attrs=dict(
            form=Bundle(
                code=Bundle(
                    text=lambda: '301952613',
                ),
            ),
            mw=aqt.mw,
        ),
        fail=lambda message: aqt.utils.showCritical(message, aqt.mw),
    ),
    logger=logger,
    paths=Bundle(
        cache=paths.CACHE,
        is_link=paths.ADDON_IS_LINKED,
    ),
    router=router,
    strip=Bundle(
        # n.b. cloze substitution logic happens first in both modes because:
        # - we need the <span>...</span> markup in on-the-fly to identify it
        # - Anki won't recognize cloze w/ HTML beginning/ending within braces
        # - the following STRIP_HTML step will cleanse the HTML out anyway

        # for content directly from a note field (e.g. BrowserGenerator runs,
        # prepopulating a modal input based on some note field, where cloze
        # placeholders are still in their unprocessed state)
        from_note=lambda text:
            COLLAPSE_WHITESPACE(
            COLLAPSE_ELLIPSES(
            SPEC_ELLIP_NOTE(
            SPEC_COUNT_NOTE(
            SPEC_STRIP_NOTE(
            STRIP_CONDITIONALLY_NOTE(
            STRIP_FILENAMES(
            STRIP_SOUNDS(
            STRIP_HTML(
            SUB_CLOZES_NOTE(
                text
            )))))))))),

        # for cleaning up already-processed HTML templates (e.g. on-the-fly,
        # where cloze is marked with <span class=cloze></span> tags)
        from_template=lambda text:
            COLLAPSE_WHITESPACE(
            COLLAPSE_ELLIPSES(
            SPEC_ELLIP_TEMPLATE(
            SPEC_COUNT_TEMPLATE(
            SPEC_STRIP_TEMPLATE(
            STRIP_CONDITIONALLY_TEMPLATE(
            STRIP_FILENAMES(
            STRIP_SOUNDS(
            STRIP_HTML(
            SUB_CLOZES_TEMPLATE(
                text
            )))))))))),

        # for cleaning up text from unknown sources (e.g. system clipboard)
        from_unknown=lambda text:
            COLLAPSE_WHITESPACE(
            COLLAPSE_ELLIPSES(
            SPEC_ELLIP_TEMPLATE(
            SPEC_ELLIP_NOTE(
            SPEC_COUNT_TEMPLATE(
            SPEC_COUNT_NOTE(
            SPEC_STRIP_TEMPLATE(
            SPEC_STRIP_NOTE(
            STRIP_CONDITIONALLY_TEMPLATE(
            STRIP_CONDITIONALLY_NOTE(
            STRIP_FILENAMES(
            STRIP_SOUNDS(
            STRIP_HTML(
            SUB_CLOZES_TEMPLATE(
            SUB_CLOZES_NOTE(
                text
            ))))))))))))))),

        # for direct user input (e.g. previews, EditorGenerator insertion)
        from_user=lambda text:
            COLLAPSE_WHITESPACE(
            COLLAPSE_ELLIPSES(
                text
            )),

        # target sounds specifically
        sounds=Bundle(
            # using Anki's method (used if we need to reproduce how Anki does
            # something, e.g. when Reviewer emulates {{FrontSide}})
            anki=anki.sound.stripSounds,

            # using AwesomeTTS's method (which has access to a precompiled re
            # object, usable for everything else, e.g. when BrowserGenerator
            # or BrowserStripper need to remove old sounds)
            atts=STRIP_SOUNDS,
        ),

        filenames=STRIP_FILENAMES,
    ),
    updates=updates,
    version=VERSION,
    web=WEB,
)

reviewer = gui.Reviewer(
    addon=addon,
    playback=Bundle(
        auto_question=PLAY_ONTHEFLY_QUESTION,
        auto_answer=PLAY_ONTHEFLY_ANSWER,
        shortcut=PLAY_ONTHEFLY_SHORTCUT,
    ),
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

reviewer_filter = gui.Filter(
    relay=lambda event: reviewer.key_handler(
        key_event=event,
        state=aqt.mw.reviewer.state,
        card=aqt.mw.reviewer.card,
        replay_audio=aqt.mw.reviewer.replayAudio,
    ),
    when=lambda event:
        aqt.mw.state == 'review' and
        event.type() == QEvent.KeyPress and
        not event.isAutoRepeat() and
        not event.spontaneous(),
)
aqt.mw.installEventFilter(reviewer_filter)

gui.Action(
    target=Bundle(
        constructor=gui.Configurator,
        args=(),
        kwargs=dict(addon=addon, parent=aqt.mw),
    ),
    text="Awesome&TTS...",
    sequence=sequences['configurator'],
    parent=aqt.mw.form.menuTools,
)

anki.hooks.addHook(
    'browser.setupMenus',
    lambda browser: (
        gui.Action(
            target=Bundle(
                constructor=gui.BrowserGenerator,
                args=(),
                kwargs=dict(
                    browser=browser,
                    addon=addon,
                    playback=PLAY_PREVIEW,
                    alerts=aqt.utils.showWarning,
                    parent=browser,
                ),
            ),
            text="Add Audio to Selected w/ Awesome&TTS...",
            sequence=sequences['browser_generator'],
            parent=browser.form.menuEdit,
        ),
        gui.Action(
            target=Bundle(
                constructor=gui.BrowserStripper,
                args=(),
                kwargs=dict(
                    browser=browser,
                    addon=addon,
                    alerts=aqt.utils.showWarning,
                    parent=browser,
                ),
            ),
            text="Remove Audio from Selected w/ AwesomeTTS...",
            sequence=sequences['browser_stripper'],
            parent=browser.form.menuEdit,
        ),
    ),
)
aqt.browser.Browser.updateTitle = anki.hooks.wrap(
    aqt.browser.Browser.updateTitle,
    lambda browser: [
        action.setEnabled(
            bool(browser.form.tableView.selectionModel().selectedRows())
        )
        for action in browser.findChildren(gui.Action)
    ],
    'before',
)

anki.hooks.addHook(
    'setupEditorButtons',
    lambda editor: editor.iconsBox.addWidget(
        gui.Button(
            tooltip="Record and insert an audio clip here w/ AwesomeTTS",
            sequence=sequences['editor_generator'],
            target=Bundle(
                constructor=gui.EditorGenerator,
                args=(),
                kwargs=dict(
                    editor=editor,
                    addon=addon,
                    playback=PLAY_PREVIEW,
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
        # today, the card layout for regular notes has 7 buttons/stretchers
        # and the one for cloze notes has 6 (as it lacks the "Flip" button);
        # position 3 puts our button after "Add Field", but in the event that
        # the form suddenly has a different number of buttons, let's just
        # fallback to the far left position
        3 if card_layout.buttons.count() in [6, 7] else 0,
        gui.Button(
            text="Add &TTS",
            tooltip="Insert a tag for on-the-fly playback w/ AwesomeTTS",
            sequence=sequences['templater'],
            target=Bundle(
                constructor=gui.Templater,
                args=(),
                kwargs=dict(
                    card_layout=card_layout,
                    addon=addon,
                    playback=PLAY_PREVIEW,
                    alerts=aqt.utils.showWarning,
                    parent=card_layout,
                ),
            ),
        ),
    ),
    'after',  # must use 'after' so that 'buttons' attribute is set
)


# Automatic check for new version, if enabled and not postponed/ignored

# By using the profilesLoaded hook, we do not run the update until the user is
# actually in a profile, which guarantees the main window has been loaded.
# Without the main window, update components (e.g. aqt.downloader.download,
# aqt.addons.GetAddons) that depend on it might fail unexpectedly.

if (
    config['updates_enabled'] and
    (not config['updates_postpone'] or config['updates_postpone'] <= time())
):
    anki.hooks.addHook(
        'profileLoaded',
        lambda: updates.used() or updates.check(
            callbacks=dict(
                need=lambda version, info:
                    None if config['updates_ignore'] == version
                    else [
                        updater.show()
                        for updater in [gui.Updater(
                            version=version,
                            info=info,
                            addon=addon,
                            parent=aqt.mw,
                        )]
                    ],
            ),
        ),
    )

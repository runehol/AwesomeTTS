# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2013-2014  Dave Shifflett
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
Interaction with the Anki reviewer

This module is mostly headless. It lives in the "gui" package, however,
because interacts with the GUI components of Anki and it also spawns
alert windows. It also may have more visual components in the future.
"""

__all__ = ['Reviewer']

import re

from BeautifulSoup import BeautifulSoup
from PyQt4.QtCore import Qt

from .common import key_event_combo


# n.b. Previously, before playing handlers, these event handlers checked to
# make sure that 'not sound.hasSound()'. I am guessing that this was done
# because AwesomeTTS did not know how to properly deal with multiple sounds
# at the time and they would play simultaneously.
#
# FIXME. It is possible, I suppose, that people might have the exact same
# audio file on a card via a [sound:xxx] tag as they do as a <tts> template
# tag. We can probably detect this by seeing if two of the same hashed
# filename end up in the queue (and I say "filename" because one would be
# coming from the media directory and another would be coming from the cache
# directory). This would probably need to be fixed in the router by having the
# router examine whether the exact same hashed filename is in the Anki
# playback queue already or looking at any [sound:xxx] tags on the card before
# playing back the on-the-fly sound.
#
# A similar problem probably exists in reviewer_key_handler for folks who
# includes their question card template within their answer card template and
# whose tts_key_q == tts_key_a.
#
# Unfortunately, it looks like inspecting anki.sound.mplayerQueue won't work
# out on Windows because the path gets blown away by the temporary file
# creation code.
#
# ALTERNATIVELY, if examination of the tag or playback queue turns out to not
# work out so well, checking sound.hasSound() could become two checkbox
# options on the "On-the-Fly Mode" tab for both question and answer sides.


class Reviewer(object):
    """
    Provides interaction for on-the-fly functionality and Anki's
    reviewer mode.
    """

    RE_LEGACY_TAGS = re.compile(
        r'\[\s*(\w?)\s*tts\s*:([^\[\]]+)',
        re.MULTILINE | re.IGNORECASE,
    )

    RE_ANSWER_DIVIDER = re.compile(
        # allows extra whitespace, optional quotes, and optional self-closing
        r'<\s*hr\s+id\s*=\s*.?\s*answer\s*.?\s*/?\s*>',
        re.IGNORECASE,
    )

    __slots__ = [
        '_addon',
        '_alerts',
        '_parent',
    ]

    def __init__(self, addon, alerts, parent):
        self._addon = addon
        self._alerts = alerts
        self._parent = parent

    def card_handler(self, state, card):
        """
        Examines the state the of the reviewer and whether automatic
        questions or answers are enabled, passing off to the internal
        playback method if so.
        """

        if state == 'question' and self._addon.config['automatic_questions']:
            self._play_html('front', card.q(),
                            self._addon.player.otf_question)

        elif state == 'answer' and self._addon.config['automatic_answers']:
            self._play_html('back', self._get_answer(card),
                            self._addon.player.otf_answer)

    def key_handler(self, key_event, state, card, replay_audio):
        """
        Examines the key event to see if the user has triggered one of
        the shortcut options.

        If we do not handle the key here, then it is passed through to
        the normal Anki Reviewer implementation.

        As a special case, if the user sets his/her shortcut to one of
        the built-in audio shorts (i.e. R, F5), will play ALL sounds,
        starting with the built-in ones.
        """

        if state not in ['answer', 'question']:
            return False

        combo = key_event_combo(key_event)
        if not combo:
            return False

        handled = False

        if combo in [Qt.Key_R, Qt.Key_F5]:
            replay_audio()
            handled = True

        question_combo = self._addon.config['tts_key_q']
        if question_combo and combo == question_combo:
            self._play_html('front', card.q(),
                            self._addon.player.otf_shortcut)
            handled = True

        answer_combo = self._addon.config['tts_key_a']
        if state == 'answer' and answer_combo and combo == answer_combo:
            self._play_html('back', self._get_answer(card),
                            self._addon.player.otf_shortcut)
            handled = True

        return handled

    def _get_answer(self, card):
        """
        Attempts to strip out the question side of the card in the blob
        of HTML we get as the "answer" HTML.

        This is done in three ways:
            - remove question HTML (verbatim)
            - remove question HTML (with any [sound:xxx] tags stripped),
              which is how Anki does {{FrontSide}} on the answer side
            - find any <hr id=answer> tag, and chop off anything leading
              up to the first such tag
        """

        question_html = card.q()

        answer_html = self.RE_ANSWER_DIVIDER.split(
            card.a().
            replace(question_html, '').
            replace(self._addon.strip.sounds.anki(question_html), ''),

            1,  # remove at most one segment in the event of multiple dividers
        ).pop().strip()

        self._addon.logger.debug("Reinterpreted answer HTML as:\n%s" % (
            "\n".join("<<< " + line for line in answer_html.split("\n"))
        ))

        return answer_html

    def _play_html(self, side, html, playback):
        """
        Read in the passed HTML, attempt to discover <tts> tags in it,
        and pass them to the router for processing.

        Additionally, old-style [GTTS], [TTS], and [ATTS] tags are
        detected and played back, e.g.

            - [GTTS:voice:text] or [TTS:g:voice:text] for Google TTS
            - [TTS:espeak:voice:text] for eSpeak
        """

        assert side in ['front', 'back'], "invalid 'side' passed"
        from_template = (self._addon.strip.from_template_back if side == 'back'
                         else self._addon.strip.from_template_front)

        for tag in BeautifulTTS(html)('tts'):
            self._play_html_tag(tag, from_template, playback)

        for legacy in self.RE_LEGACY_TAGS.findall(html):
            self._play_html_legacy(legacy, from_template, playback)

    def _play_html_tag(self, tag, from_template, playback):
        """Helper method for _play_html()."""

        text = from_template(unicode(tag))
        if not text:
            return

        attr = dict(tag.attrs)

        try:
            svc_id = attr.pop('service')
        except KeyError:
            self._alerts(
                "This tag needs a 'service' attribute:\n%s" %
                tag.prettify().decode('utf-8'),
                self._parent,
            )
            return

        self._addon.router(
            svc_id=svc_id,
            text=text,
            options=attr,
            callbacks=dict(
                okay=playback,
                fail=lambda exception: (
                    # we can safely ignore "service busy" errors in review
                    isinstance(exception, self._addon.router.BusyError) or
                    self._alerts(
                        "Unable to play this tag:\n%s\n\n%s" % (
                            tag.prettify().decode('utf-8').strip(),
                            exception.message,
                        ),
                        self._parent,
                    )
                ),
            ),
        )

    def _play_html_legacy(self, legacy, from_template, playback):
        """Helper method for _play_html()."""

        components = legacy[1].split(':')

        if legacy[0] and legacy[0].strip().lower() == 'g':
            if len(components) < 2:
                self._play_html_legacy_bad(
                    legacy,
                    "Old-style GTTS bracket tags must specify the "
                    "voice, e.g. [GTTS:es:hola], [GTTS:es:{{Front}}], "
                    "[GTTS:en:{{text:Back}}]",
                )
                return

            svc_id = 'google'

        else:
            if len(components) < 3:
                self._play_html_legacy_bad(
                    legacy,
                    "Old-style TTS bracket tags must specify service and "
                    "voice, e.g. [TTS:g:es:mundo], [TTS:g:es:{{Front}}], "
                    "[TTS:g:en:{{text:Back}}]",
                )
                return

            svc_id = components.pop(0)

        voice = components.pop(0)

        text = ':'.join(components)
        text = from_template(text)
        if not text:
            return

        self._addon.router(
            svc_id=svc_id,
            text=text,
            options={'voice': voice},
            callbacks=dict(
                okay=playback,
                fail=lambda exception: (
                    isinstance(exception, self._addon.router.BusyError) or
                    self._play_html_legacy_bad(legacy, exception.message)
                ),
            ),
        )

    def _play_html_legacy_bad(self, legacy, message):
        """Reassembles the legacy given tag and displays an alert."""

        self._alerts(
            "Unable to play this tag:\n[%sTTS:%s]\n\n%s" %
            (legacy[0], legacy[1], message),
            self._parent,
        )

    def selection_handler(self, text, preset):
        """Play the selected text using the preset."""

        self._addon.router(
            svc_id=preset['service'],
            text=text,
            options=preset,
            callbacks=dict(
                okay=self._addon.player.menu_click,
                fail=lambda exception: (
                    isinstance(exception, self._addon.router.BusyError) or
                    self._alerts(exception.message, self._parent)
                ),
            ),
        )


class BeautifulTTS(BeautifulSoup):  # pylint:disable=too-many-public-methods
    """
    Provides a customized version of the BeautifulSoup parser that
    treats TTS tags as nestable.
    """

    NESTABLE_TAGS = dict(BeautifulSoup.NESTABLE_TAGS.items() +
                         [('tts', [])])

# -*- coding: utf-8 -*-

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
Basic manipulation and sanitization of input text
"""

__all__ = ['RE_CLOZE_BRACED', 'RE_ELLIPSES', 'RE_FILENAMES', 'RE_SOUNDS',
           'RE_WHITESPACE', 'STRIP_HTML', 'Sanitizer']

import re
import anki


RE_CLOZE_BRACED = re.compile(anki.template.template.clozeReg % r'\d+')
RE_CLOZE_RENDERED = re.compile(
    # see anki.template.template.clozeText; n.b. the presence of the brackets
    # in the pattern means that this will only match and replace on the
    # question side of cards
    r'<span class=.?cloze.?>\[(.+?)\]</span>'
)
RE_ELLIPSES = re.compile(r'\s*(\.\s*){3,}')
RE_FILENAMES = re.compile(r'[a-z\d]+(-[a-f\d]{8}){5}( \(\d+\))?\.mp3')
RE_SOUNDS = re.compile(r'\[sound:(.*?)\]')  # see also anki.sound._soundReg
RE_WHITESPACE = re.compile(r'[\0\s]+')

STRIP_HTML = anki.utils.stripHTML  # this also converts character entities


class Sanitizer(object):  # call only, pylint:disable=too-few-public-methods
    """Once instantiated, provides a callable to sanitize text."""

    # _rule_xxx() methods are in-class for getattr, pylint:disable=no-self-use

    __slots__ = [
        '_config',  # dict-like interface for looking up config conditionals
        '_logger',  # logger-like interface for debugging the Sanitizer
        '_rules',   # list of rules that this instance's callable will process
    ]

    def __init__(self, rules, config=None, logger=None):
        self._rules = rules
        self._config = config
        self._logger = logger

    def __call__(self, text):
        """Apply the initialized rules against the text and return."""

        applied = []

        for rule in self._rules:
            if isinstance(rule, basestring):  # always run these rules
                applied.append(rule)
                text = getattr(self, '_rule_' + rule)(text)

            elif isinstance(rule, tuple):  # rule that depends on config
                try:
                    addl = rule[2]
                except IndexError:
                    addl = None
                key = rule[1]
                rule = rule[0]

                value = self._config[key]

                if value is True:  # basic on/off config flag
                    if addl:
                        addl = self._config[addl]
                        applied.append((rule, addl))
                        text = getattr(self, '_rule_' + rule)(text, addl)

                    else:
                        applied.append(rule)
                        text = getattr(self, '_rule_' + rule)(text)

                elif value:  # some other truthy value that drives the rule
                    if addl:
                        addl = self._config[addl]
                        applied.append((rule, value, addl))
                        text = getattr(self, '_rule_' + rule)(text, value,
                                                              addl)

                    else:
                        applied.append((rule, value))
                        text = getattr(self, '_rule_' + rule)(text, value)

            else:
                raise AssertionError("bad rule given to Sanitizer instance")

        if self._logger:
            self._logger.debug("Transformation using %s: %s", applied, text)

        return text

    def _rule_clozes_braced(self, text, mode):
        """
        Given a braced cloze placeholder in a note, examine the option
        mode and return an appropriate replacement.
        """

        return RE_CLOZE_BRACED.sub(
            '...' if mode == 'ellipsize'
            else '' if mode == 'remove'
            else self._rule_clozes_braced.wrapper if mode == 'wrap'
            else self._rule_clozes_braced.deleter if mode == 'deleted'
            else self._rule_clozes_braced.ankier,  # mode == 'anki'

            text,
        )

    _rule_clozes_braced.wrapper = lambda match: (
        '... %s ...' % match.group(3).strip('.') if (match.group(3) and
                                                     match.group(3).strip('.'))
        else '...'
    )

    _rule_clozes_braced.deleter = lambda match: (
        match.group(1) if match.group(1)
        else '...'
    )

    _rule_clozes_braced.ankier = lambda match: (
        match.group(3) if match.group(3)
        else '...'
    )

    def _rule_clozes_rendered(self, text, mode):
        """
        Given a rendered cloze HTML tag, examine the option mode and
        return an appropriate replacement.
        """

        return RE_CLOZE_RENDERED.sub(
            '...' if mode == 'ellipsize'
            else '' if mode == 'remove'
            else self._rule_clozes_rendered.wrapper if mode == 'wrap'
            else self._rule_clozes_rendered.ankier,  # mode == 'anki'

            text,
        )

    _rule_clozes_rendered.wrapper = lambda match: (
        '... %s ...' % match.group(1).strip('.')
        if match.group(1).strip('.')
        else match.group(1)
    )

    _rule_clozes_rendered.ankier = lambda match: match.group(1)

    def _rule_counter(self, text, characters, wrap):
        """
        Upon encountering the given characters, replace with the number
        of those characters that were encountered.
        """

        return re.sub(
            r'[' + re.escape(characters) + ']{2,}',

            self._rule_counter.wrapper if wrap
            else self._rule_counter.spacer,

            text,
        )

    _rule_counter.wrapper = lambda match: (' ... ' + str(len(match.group(0))) +
                                           ' ... ')

    _rule_counter.spacer = lambda match: (' ' + str(len(match.group(0))) + ' ')

    def _rule_ellipses(self, text):
        """
        Given at least three periods, separated by whitespace or not,
        collapse down to three consecutive periods padded on both sides.
        """

        return RE_ELLIPSES.sub(' ... ', text)

    def _rule_filenames(self, text):
        """
        Removes any filenames that appear to be from AwesomeTTS.
        """

        return RE_FILENAMES.sub('', text)

    def _rule_html(self, text):
        """
        Removes any HTML, including converting character entities.
        """

        return STRIP_HTML(text)

    def _rule_sounds_ours(self, text):
        """
        Removes sound tags that appear to be from AwesomeTTS.
        """

        return RE_SOUNDS.sub(
            lambda match: (
                '' if RE_FILENAMES.match(match.group(1))
                else match.group(0)
            ),
            text,
        )

    def _rule_sounds_theirs(self, text):
        """
        Removes sound tags that appear to NOT be from AwesomeTTS.
        """

        return RE_SOUNDS.sub(
            lambda match: (
                match.group(0) if RE_FILENAMES.match(match.group(1))
                else ''
            ),
            text,
        )

    def _rule_sounds_univ(self, text):
        """
        Removes sound tags, regardless of origin.
        """

        return RE_SOUNDS.sub('', text)

    def _rule_whitespace(self, text):
        """
        Collapses all whitespace down to a single space and strips
        off any leading or trailing whitespace.
        """

        return RE_WHITESPACE.sub(' ', text).strip()

    def _aux_within(self, text, begin_char, end_char):
        """
        Removes any substring of text that starts with begin_char and
        ends with end_char.
        """

        return text  # TODO

    _rule_within_braces = lambda self, text: self._aux_within(text, '{', '}')

    _rule_within_brackets = lambda self, text: self._aux_within(text, '[', ']')

    _rule_within_parens = lambda self, text: self._aux_within(text, '(', ')')

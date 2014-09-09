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

__all__ = ['Sanitizer',
           'RE_ELLIPSES', 'RE_WHITESPACE']

import re


RE_ELLIPSES = re.compile(r'\s*(\.\s*){3,}')
RE_WHITESPACE = re.compile(r'[\0\s]+')


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
                rule, key = rule
                value = self._config[key]

                if value is True:  # basic on/off config flag
                    applied.append(rule)
                    text = getattr(self, '_rule_' + rule)(text)

                elif value:  # some other truthy value that drives the rule
                    applied.append((rule, value))
                    text = getattr(self, '_rule_' + rule)(text, value)

            else:
                raise AssertionError("bad rule given to Sanitizer instance")

        if self._logger:
            self._logger.debug("Transformation using %s: %s", applied, text)

        return text

    def _rule_ellipses(self, text):
        """
        Given at least three periods, separated by whitespace or not,
        collapse down to three consecutive periods padded on both sides.
        """

        return RE_ELLIPSES.sub(' ... ', text)

    def _rule_whitespace(self, text):
        """
        Collapses all whitespace down to a single space and strips
        off any leading or trailing whitespace.
        """

        return RE_WHITESPACE.sub(' ', text).strip()

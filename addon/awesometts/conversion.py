# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2013-2014  Anki AwesomeTTS Development Team
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
Helpful type conversions
"""

__all__ = ['BOOL', 'NULLABLE_INT', 'NULLABLE_KEY', 'JSON_DICT', 'NORMALIZED',
           'compact_json', 'substitution_compiled', 'substitution_json',
           'substitution_list']

import json
import re

from PyQt4.QtCore import Qt


# TODO: Rename and convert to regular functions with more fault tolerance

BOOL = lambda value: bool(int(value))  # workaround for bool('0') == True

NULLABLE_INT = lambda value: int(value) if value else None

NULLABLE_KEY = lambda value: Qt.Key(value) if value else None

JSON_DICT = lambda value: isinstance(value, basestring) and \
    value.lstrip().startswith('{') and json.loads(value) or {}

NORMALIZED = lambda value: ''.join(
    char.lower()
    for char in value
    if char.isalpha() or char.isdigit()
)

# END TODO


def compact_json(obj):
    """Given an object, return a minimal JSON-encoded string."""

    return json.dumps(obj, separators=compact_json.SEPARATORS)

compact_json.SEPARATORS = (',', ':')


def substitution_compiled(rule):
    """
    Given a substitution rule, returns a compiled matcher object using
    re.compile(). Because advanced substitutions execute after all
    whitespace is collapsed, neither re.DOTALL nor re.MULTILINE need to
    be supported here.
    """

    return re.compile(
        pattern=rule['input'] if rule['regex'] else re.escape(rule['input']),
        flags=sum(
            value
            for key, value in [('ignore_case', re.IGNORECASE),
                               ('unicode', re.UNICODE)]
            if rule[key]
        ),
    )


def substitution_json(rules):
    """
    Given a list of substitution rules, filters out the compiled member
    from each rule and returns the list serialized as JSON.
    """

    return (
        compact_json([
            dict((key, value)
                 for key, value
                 in item.items()
                 if key != 'compiled')
            for item in rules
        ])
        if rules and isinstance(rules, list)
        else '[]'
    )


def substitution_list(json_str):
    """
    Given a JSON string, returns a list of valid substitution rules with
    each rule's 'compiled' member instantiated.
    """

    try:
        candidates = json.loads(json_str)
        if not isinstance(candidates, list):
            raise ValueError

    except StandardError:
        return []

    rules = []

    for candidate in candidates:
        if not ('replace' in candidate and
                isinstance(candidate['replace'], basestring)):
            continue

        for key, default in [('regex', False),
                             ('ignore_case', True),
                             ('unicode', True)]:
            if key not in candidate:
                candidate[key] = default

        try:
            candidate['compiled'] = substitution_compiled(candidate)
        except Exception:  # sre_constants.error, pylint:disable=broad-except
            continue

        rules.append(candidate)

    return rules

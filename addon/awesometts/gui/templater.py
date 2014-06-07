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
Template generation dialog
"""

__all__ = ['Templater']

from PyQt4 import QtCore, QtGui

from .base import ServiceDialog

# all methods might need 'self' in the future, pylint:disable=R0201


class Templater(ServiceDialog):
    """
    Provides a dialog for building an on-the-fly TTS tag in Anki's card
    layout editor.
    """

    __slots__ = [
        '_card_layout',  # reference to the card layout window
        '_is_cloze',     # True if the model attached
    ]

    def __init__(self, card_layout, *args, **kwargs):
        """
        Sets our title.
        """

        from anki.consts import MODEL_CLOZE
        self._card_layout = card_layout
        self._is_cloze = card_layout.model['type'] == MODEL_CLOZE

        super(Templater, self).__init__(
            title="Add On-the-Fly TTS Tag to Template",
            *args, **kwargs
        )

    # UI Construction ########################################################

    def _ui_control(self):
        """
        Returns the superclass's text and preview buttons, adding our
        field input selector, then the base class's cancel/OK buttons.
        """

        header = QtGui.QLabel("Tag Options")
        header.setFont(self._FONT_HEADER)

        intro = QtGui.QLabel(
            "In review mode, AwesomeTTS can automatically read the text from "
            "any <tts> tags in the template, generating on-the-fly audio "
            "playback. You can specify a specific note field to read from or "
            "customize the text yourself."
        )
        intro.setTextFormat(QtCore.Qt.PlainText)
        intro.setWordWrap(True)

        hint = QtGui.QLabel(
            "Normally, the content of <tts> tags are visible like any other "
            "HTML tag, but you can alter their appearance with inline CSS or "
            "the shared style rules."
        )
        hint.setTextFormat(QtCore.Qt.PlainText)
        hint.setWordWrap(True)

        layout = super(Templater, self)._ui_control()
        layout.addWidget(header)
        layout.addWidget(intro)
        layout.addWidget(hint)
        layout.addLayout(self._ui_control_fields())
        layout.addWidget(self._ui_buttons())

        return layout

    def _ui_control_fields(self):
        """
        Returns a dropdown box to let the user select a source field.
        """

        widgets = {}
        layout = QtGui.QGridLayout()

        for row, label, name, options in [
            (0, "Field:", 'field', [
                ('', "customize the tag's content"),
            ] + [
                (field, field)
                for field in sorted({
                    field['name']
                    for field in self._card_layout.model['flds']
                })
            ]),

            (1, "Visibility:", 'hide', [
                ('normal', "insert the tag as-is"),
                ('inline', "hide just this tag w/ inline CSS"),
                ('global', "add rule to hide any TTS tag for this note type"),
            ]),

            (2, "Add to:", 'target', [
                ('front', "Front Template"),
                ('back', "Back Template"),
            ]),

            # row 3 is used below if self._is_cloze is True
        ]:
            label = QtGui.QLabel(label)
            label.setFont(self._FONT_LABEL)

            widgets[name] = self._ui_control_fields_dropdown(name, options)
            layout.addWidget(label, row, 0)
            layout.addWidget(widgets[name], row, 1)

        if self._is_cloze:
            cloze = QtGui.QCheckBox()
            cloze.setObjectName('cloze')
            cloze.setMinimumHeight(25)

            warning = QtGui.QLabel("Remember 'cloze:' for any cloze fields.")
            warning.setMinimumHeight(25)

            layout.addWidget(cloze, 3, 1)
            layout.addWidget(warning, 3, 1)

            widgets['field'].setCurrentIndex(-1)
            widgets['field'].currentIndexChanged.connect(lambda index: (
                cloze.setVisible(index),
                cloze.setText(
                    "%s uses cloze" %
                    (widgets['field'].itemData(index) if index else "this")
                ),
                warning.setVisible(not index),
            ))

        return layout

    def _ui_control_fields_dropdown(self, name, options):
        """
        Returns a dropdown with the given list of options.
        """

        dropdown = QtGui.QComboBox()
        dropdown.setObjectName(name)
        for value, label in options:
            dropdown.addItem(label, value)

        return dropdown

    def _ui_buttons(self):
        """
        Adjust title of the OK button.
        """

        buttons = super(Templater, self)._ui_buttons()
        buttons.findChild(QtGui.QAbstractButton, 'okay').setText("&Insert")

        return buttons

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Restore the three dropdown's last known state and then focus the
        field dropdown.
        """

        super(Templater, self).show(*args, **kwargs)

        for name in ['hide', 'target', 'field']:
            dropdown = self.findChild(QtGui.QComboBox, name)
            dropdown.setCurrentIndex(max(
                dropdown.findData(self._addon.config['templater_' + name]), 0
            ))

        if self._is_cloze:
            self.findChild(QtGui.QCheckBox, 'cloze') \
                .setChecked(self._addon.config['templater_cloze'])

        dropdown.setFocus()  # abuses fact that 'field' is last in the loop

    def accept(self):
        """
        Given the user's selected service and options, assembles a TTS
        tag and then remembers the options.
        """

        now = self._get_all()
        tform = self._card_layout.tab['tform']

        from cgi import escape
        target = getattr(tform, now['templater_target'])
        target.setPlainText('\n'.join([
            target.toPlainText(),
            '<tts service="%s" %s>%s</tts>' % (
                now['last_service'],

                ' '.join([
                    '%s="%s"' % (key, escape(str(value)))
                    for key, value in
                        now['last_options'][now['last_service']].items()
                        + (
                            [('style', 'display: none')]
                            if now['templater_hide'] == 'inline' else []
                        )
                ]),

                (
                    (
                        '{{cloze:%s}}' if now.get('templater_cloze')
                        else '{{%s}}'
                    ) % now['templater_field']
                ) if now['templater_field']
                else '',
            ),
        ]))

        if now['templater_hide'] == 'global':
            existing_css = tform.css.toPlainText()
            extra_css = 'tts { display: none }'
            if existing_css.find(extra_css) < 0:
                tform.css.setPlainText('\n'.join([
                    existing_css,
                    extra_css,
                ]))

        self._addon.config.update(now)
        super(Templater, self).accept()

    def _get_all(self):
        """
        Adds support to remember the three dropdowns and cloze state (if any),
        in addition to the service options handled by the superclass.
        """

        combos = {
            name: widget.itemData(widget.currentIndex())
            for name in ['field', 'hide', 'target']
            for widget in [self.findChild(QtGui.QComboBox, name)]
        }

        return dict(
            super(Templater, self)._get_all().items() +
            [('templater_' + name, value) for name, value in combos.items()] +
            (
                [(
                    'templater_cloze',
                    self.findChild(QtGui.QCheckBox, 'cloze').isChecked(),
                )]
                if self._is_cloze and combos['field']
                else []
            )
        )

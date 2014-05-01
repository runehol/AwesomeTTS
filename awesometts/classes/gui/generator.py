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
File generation dialogs
"""

__all__ = ['BrowserGenerator', 'EditorGenerator']

from PyQt4 import QtGui

from .base import ServiceDialog


class BrowserGenerator(ServiceDialog):
    """
    Provides a dialog for generating many media files to multiple cards
    from the card browser.
    """

    __slots__ = [
        '_browser',  # reference to the current Anki browser window
        '_notes',    # the list of Note objects selected when window opened
    ]

    def __init__(self, browser, *args, **kwargs):
        """
        Sets our title.
        """

        self._browser = browser
        self._notes = None  # set in show()

        super(BrowserGenerator, self).__init__(*args, **kwargs)
        self.setWindowTitle("Mass Generate MP3s w/ %s" % self.windowTitle())

    # UI Construction ########################################################

    def _ui_control(self):
        """
        Returns the superclass's text and preview buttons, adding our
        inputs to control the mass generation process, and then the base
        class's cancel/OK buttons.
        """

        header = QtGui.QLabel("Fields and Handling")
        header.setFont(self._FONT_HEADER)

        intro = QtGui.QLabel(
            "AwesomeTTS will read the text in the source field, generate an "
            "MP3 file, and place it into the destination field."
        )
        intro.setFont(self._FONT_INFO)
        intro.setWordWrap(True)

        layout = super(BrowserGenerator, self)._ui_control()
        layout.addWidget(header)
        layout.addWidget(intro)
        layout.addLayout(self._ui_control_fields())
        layout.addWidget(self._ui_control_handling())
        layout.addWidget(self._ui_buttons())

        return layout

    def _ui_control_fields(self):
        """
        Returns a grid layout with the source and destination fields.

        Note that populating the field dropdowns is deferred to the
        show() event handler because the available fields might change
        from call to call.
        """

        source_label = QtGui.QLabel("Source Field:")
        source_label.setFont(self._FONT_LABEL)

        source_dropdown = QtGui.QComboBox()
        source_dropdown.setObjectName('source')

        dest_label = QtGui.QLabel("Destination Field:")
        dest_label.setFont(self._FONT_LABEL)

        dest_dropdown = QtGui.QComboBox()
        dest_dropdown.setObjectName('dest')

        layout = QtGui.QGridLayout()
        layout.addWidget(source_label, 0, 0)
        layout.addWidget(source_dropdown, 0, 1)
        layout.addWidget(dest_label, 1, 0)
        layout.addWidget(dest_dropdown, 1, 1)

        return layout

    def _ui_control_handling(self):
        """
        Return the append/overwrite radio buttons and behavior checkbox.
        """

        append = QtGui.QRadioButton(
            "&Append [sound:xxx] Tag onto Destination Field"
        )
        append.setObjectName('append')
        append.toggled.connect(self._on_handling_toggled)

        overwrite = QtGui.QRadioButton(
            "Over&write the Destination Field w/ Media Filename"
        )
        overwrite.setObjectName('overwrite')
        overwrite.toggled.connect(self._on_handling_toggled)

        behavior = QtGui.QCheckBox()
        behavior.setObjectName('behavior')

        layout = QtGui.QVBoxLayout()
        layout.addWidget(append)
        layout.addWidget(overwrite)
        layout.addWidget(behavior)

        widget = QtGui.QWidget()
        widget.setLayout(layout)

        return widget

    def _ui_buttons(self):
        """
        Adjust title of the OK button.
        """

        buttons = super(BrowserGenerator, self)._ui_buttons()
        buttons.findChild(QtGui.QAbstractButton, 'okay').setText("&Generate")

        return buttons

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Populate the source and destination dropdowns, recall the
        handling and behavior inputs, and focus the source dropdown.

        Note that the fields are dumped and repopulated each time,
        because the list of fields might change between displays of the
        window.
        """

        # FIXME. For a very large selectedNotes() set, doing this might be too
        # slow. An alternative might be to load the form UI, disable all the
        # input controls, display a message, load the notes in another thread,
        # then re-enable the input controls.

        self._notes = [
            self._browser.mw.col.getNote(note_id)
            for note_id in self._browser.selectedNotes()
        ]

        fields = sorted({
            field
            for note in self._notes
            for field in note.keys()
        })

        config = self._addon.config

        source = self.findChild(QtGui.QComboBox, 'source')
        source.clear()
        source.addItems(fields)
        try:
            source.setCurrentIndex(fields.index(config['last_mass_source']))
        except ValueError:
            pass

        dest = self.findChild(QtGui.QComboBox, 'dest')
        dest.clear()
        dest.addItems(fields)
        try:
            dest.setCurrentIndex(fields.index(config['last_mass_dest']))
        except ValueError:
            pass

        self.findChild(
            QtGui.QRadioButton,
            'append' if self._addon.config['last_mass_append']
            else 'overwrite',
        ).setChecked(True)

        self.findChild(QtGui.QCheckBox, 'behavior') \
            .setChecked(self._addon.config['last_mass_behavior'])

        super(BrowserGenerator, self).show(*args, **kwargs)

        source.setFocus()

    def accept(self, *args, **kwargs):
        """
        TODO
        """

        source, dest = self._get_field_values()

        eligible_notes = [
            note
            for note in self._notes
            if source in note.keys() and dest in note.keys()
        ]

        if not eligible_notes:
            self._alerts(
                "Of the %d notes selected in the browser, none have both "
                "'%s' and '%s' fields." % (len(self._notes), source, dest)
                if len(self._notes) > 1
                else "The selected note does not have both '%s' and '%s'"
                    "fields." % (source, dest),
                self,
            )
            return

        svc_id, values = self._get_service_values()


        # TODO do recording code
        # TODO update all four mass_xxx configuration settings
        # TODO double-check that Router class is setup to remember
        # the service used and its options

        super(BrowserGenerator, self).accept(*args, **kwargs)

    def _get_field_values(self):
        """
        Return the user's source and destination fields.
        """

        return (
            self.findChild(QtGui.QComboBox, 'source').currentText(),
            self.findChild(QtGui.QComboBox, 'dest').currentText(),
        )

    def _on_handling_toggled(self):
        """
        Change the text on the behavior checkbox based on the append
        or overwrite behavior.
        """

        append = self.findChild(QtGui.QRadioButton, 'append')
        behavior = self.findChild(QtGui.QCheckBox, 'behavior')
        behavior.setText(
            "Remove Existing [sound:xxx] Tag(s)" if append.isChecked()
            else "Wrap the Filename in [sound:xxx] Tag"
        )


class EditorGenerator(ServiceDialog):
    """
    Provides a dialog for adding single media files from the editors.
    """

    __slots__ = [
        '_editor',  # reference to one of the editors in the Anki GUI
    ]

    def __init__(self, editor, *args, **kwargs):
        """
        Sets our title.
        """

        self._editor = editor
        super(EditorGenerator, self).__init__(*args, **kwargs)
        self.setWindowTitle("Insert MP3 w/ %s" % self.windowTitle())

    # UI Construction ########################################################

    def _ui_control(self):
        """
        Replaces the superclass's version of this with a version that
        returns a "Preview and Record" header, larger text input area,
        and preview button on its own line.
        """

        header = QtGui.QLabel("Preview and Record")
        header.setFont(self._FONT_HEADER)

        text = QtGui.QPlainTextEdit()
        text.setObjectName('text')
        text.setTabChangesFocus(True)

        button = QtGui.QPushButton("&Preview")
        button.setObjectName('preview')
        button.clicked.connect(self._on_preview)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(text)
        layout.addWidget(button)
        layout.addWidget(self._ui_buttons())

        return layout

    def _ui_buttons(self):
        """
        Adjust title of the OK button.
        """

        buttons = super(EditorGenerator, self)._ui_buttons()
        buttons.findChild(QtGui.QAbstractButton, 'okay').setText("&Record")

        return buttons

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Focus the text area after displaying the dialog.
        """

        super(EditorGenerator, self).show(*args, **kwargs)

        self.findChild(QtGui.QPlainTextEdit, 'text').setFocus()

    def accept(self, *args, **kwargs):
        """
        Given the user's options and text, calls the service to make a
        recording. If successful, the options are remembered and the MP3
        inserted into the field.
        """

        svc_id, values = self._get_service_values()
        text_input, text_value = self._get_service_text()
        self._disable_inputs()

        self._addon.router(
            svc_id=svc_id,
            text=text_value,
            options=values,
            callbacks=dict(
                done=lambda: self._disable_inputs(False),
                okay=lambda path: (
                    self._addon.config.update(self._remember_values()),
                    super(EditorGenerator, self).accept(*args, **kwargs),
                    self._editor.addMedia(path),
                ),
                fail=lambda exception: (
                    self._alerts(exception.message, self),
                    text_input.setFocus(),
                ),
            ),
        )

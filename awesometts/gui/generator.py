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

from PyQt4 import QtCore, QtGui

from .base import ServiceDialog


class BrowserGenerator(ServiceDialog):
    """
    Provides a dialog for generating many media files to multiple cards
    from the card browser.
    """

    INTRO = (
        "AwesomeTTS will scan the %d note%s selected in the Browser, "
        "determine %s the source field, store the audio in your collection, "
        "and update the destination with either a [sound] tag or filename."
    )

    # TODO. It would be nice if the progress dialog shown during generation
    # offered a cancel button (labeled "Stop"). This would work just by having
    # an additional 'cancelled' flag on the _process object that we check for
    # at the beginning of _accept_next(), possibly in the same conditional as
    # the "not self._process['queue']" check. Additionally, a cancelled=True
    # flag should be passed to _accept_done() that causes the user's service
    # and handling/behavior preferences to NOT be persisted to the database.

    __slots__ = [
        '_browser',       # reference to the current Anki browser window
        '_notes',         # list of Note objects selected when window opened
        '_process',       # state during processing; see accept() method below
    ]

    def __init__(self, browser, *args, **kwargs):
        """
        Sets our title.
        """

        self._browser = browser
        self._notes = None  # set in show()
        self._process = None  # set in accept()

        super(BrowserGenerator, self).__init__(
            title="Add TTS Audio to Selected Notes",
            *args, **kwargs
        )

    # UI Construction ########################################################

    def _ui_control(self):
        """
        Returns the superclass's text and preview buttons, adding our
        inputs to control the mass generation process, and then the base
        class's cancel/OK buttons.
        """

        header = QtGui.QLabel("Fields and Handling")
        header.setFont(self._FONT_HEADER)

        intro = QtGui.QLabel(self.INTRO)
        intro.setObjectName('intro')
        intro.setWordWrap(True)

        warning = QtGui.QLabel(
            "Please note that if you use bare filenames, the 'Check Media' "
            "feature in Anki will not detect audio files as in-use, even if "
            "you insert the field into your templates."
        )
        warning.setWordWrap(True)

        layout = super(BrowserGenerator, self)._ui_control()
        layout.addWidget(header)
        layout.addWidget(intro)
        layout.addLayout(self._ui_control_fields())
        layout.addWidget(self._ui_control_handling())
        layout.addWidget(warning)
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

        self.findChild(QtGui.QLabel, 'intro').setText(
            self.INTRO % (
                len(self._notes),
                "s" if len(self._notes) != 1 else "",
                "which have" if len(self._notes) != 1 else "if it has",
            )
        )

        fields = sorted({
            field
            for note in self._notes
            for field in note.keys()
        })

        config = self._addon.config

        source = self.findChild(QtGui.QComboBox, 'source')
        source.clear()
        source.addItems(fields)
        source.setCurrentIndex(
            max(source.findData(config['last_mass_source']), 0)
        )

        dest = self.findChild(QtGui.QComboBox, 'dest')
        dest.clear()
        dest.addItems(fields)
        dest.setCurrentIndex(
            max(dest.findData(config['last_mass_dest']), 0)
        )

        self.findChild(
            QtGui.QRadioButton,
            'append' if self._addon.config['last_mass_append']
            else 'overwrite',
        ).setChecked(True)

        self.findChild(QtGui.QCheckBox, 'behavior') \
            .setChecked(self._addon.config['last_mass_behavior'])

        super(BrowserGenerator, self).show(*args, **kwargs)

        source.setFocus()

    def accept(self):
        """
        Check to make sure that we have at least one note, pull the
        service options, and kick off the processing.
        """

        source, dest, append, behavior = self._get_field_values()

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

        svc_id, options = self._get_service_values()

        self._process = {
            'service': {
                'id': svc_id,
                'options': options,
            },
            'fields': {
                'source': source,
                'dest': dest,
            },
            'handling': {
                'append': append,
                'behavior': behavior,
            },
            'queue': eligible_notes,
            'counts': {
                'total': len(self._notes),
                'elig': len(eligible_notes),
                'skip': len(self._notes) - len(eligible_notes),
                'done': 0,  # all notes processed
                'okay': 0,  # calls which resulted in a successful MP3
                'fail': 0,  # calls which resulted in an exception
            },
            'exceptions': {},
            'throttling': {
                'calls': 0,  # number of cache misses in this batch
                'sleep': self._addon.config['throttle_sleep'],
                'threshold': self._addon.config['throttle_threshold'],
            } if self._addon.router.has_trait(svc_id,
                self._addon.router.Trait.INTERNET) else False,
        }

        self._disable_inputs()

        self._browser.mw.checkpoint(
            "AwesomeTTS Batch Update (%d note%s)" % (
                self._process['counts']['elig'],
                "s" if self._process['counts']['elig'] != 1 else "",
            )
        )
        self._browser.mw.progress.start(
            min=0,
            max=self._process['counts']['elig'],
            label="Generating MP3 files...",
            parent=self,
            immediate=True,
        )
        self._browser.model.beginReset()

        self._accept_next()

    def _accept_next(self):
        """
        Pop the next note off the queue, if not throttled, and process.
        """

        self._accept_update()

        if not self._process['queue']:
            self._accept_done()
            return

        if (
            self._process['throttling'] and
            self._process['throttling']['calls'] >=
            self._process['throttling']['threshold']
        ):
            self._process['throttling']['countdown'] = \
                self._process['throttling']['sleep']

            timer = QtCore.QTimer()
            self._process['throttling']['timer'] = timer

            timer.timeout.connect(self._accept_throttled)
            timer.setInterval(1000)
            timer.start()
            return

        note = self._process['queue'].pop(0)

        def done():
            """Count the processed note."""

            self._process['counts']['done'] += 1

        def okay(path):
            """Count the success and update the note."""

            filename = self._browser.mw.col.media.addFile(path)
            dest = self._process['fields']['dest']

            if self._process['handling']['append']:
                if self._process['handling']['behavior']:
                    note[dest] = self._addon.strip.sounds(note[dest]).strip()
                note[dest] += ' [sound:%s]' % filename

            else:
                if self._process['handling']['behavior']:
                    note[dest] = '[sound:%s]' % filename
                else:
                    note[dest] = filename

            self._process['counts']['okay'] += 1
            note.flush()

        def fail(exception):
            """Count the failure and the unique message."""

            self._process['counts']['fail'] += 1

            message = exception.message
            try:
                self._process['exceptions'][message] += 1
            except KeyError:
                self._process['exceptions'][message] = 1

        callbacks = dict(
            done=done, okay=okay, fail=fail,
            then=self._accept_next,
        )

        if self._process['throttling']:
            def miss():
                """Count the cache miss."""

                self._process['throttling']['calls'] += 1

            callbacks['miss'] = miss

        self._addon.router(
            svc_id=self._process['service']['id'],
            text=note[self._process['fields']['source']],
            options=self._process['service']['options'],
            callbacks=callbacks,
        )

    def _accept_throttled(self):
        """
        Called for every "timeout" of the timer during a throttling.
        """

        self._process['throttling']['countdown'] -= 1
        self._accept_update()

        if self._process['throttling']['countdown'] <= 0:
            self._process['throttling']['timer'].stop()
            del self._process['throttling']['countdown']
            del self._process['throttling']['timer']
            self._process['throttling']['calls'] = 0
            self._accept_next()

    def _accept_update(self):
        """
        Update the progress bar and message.
        """

        self._browser.mw.progress.update(
            label="finished %d of %d%s\n"
                  "%d successful, %d failed\n"
                  "\n"
                  "%s" % (
                      self._process['counts']['done'],
                      self._process['counts']['elig'],

                      " (%d skipped)" % self._process['counts']['skip']
                      if self._process['counts']['skip']
                      else "",

                      self._process['counts']['okay'],
                      self._process['counts']['fail'],

                      "sleeping for %d second%s" % (
                          self._process['throttling']['countdown'],
                          "s"
                          if self._process['throttling']['countdown'] != 1
                          else ""
                      )
                      if (
                          self._process['throttling'] and
                          'countdown' in self._process['throttling']
                      )
                      else " "
                  ),
            value=self._process['counts']['done'],
        )

    def _accept_done(self):
        """
        Display statistics and close out the dialog.
        """

        self._browser.model.endReset()
        self._browser.mw.progress.finish()

        messages = [
            "The %d note%s you selected %s been processed. " % (
                self._process['counts']['total'],
                "s" if self._process['counts']['total'] != 1 else "",
                "have" if self._process['counts']['total'] != 1 else "has",
            )
            if self._process['counts']['done'] ==
                self._process['counts']['total']
            else "%d of the %d note%s you selected %s processed. " % (
                self._process['counts']['done'],
                self._process['counts']['total'],
                "s" if self._process['counts']['total'] != 1 else "",
                "were" if self._process['counts']['done'] != 1 else "was",
            ),

            "%d note%s skipped for not having both the source and "
            "destination fields. Of those remaining, " % (
                self._process['counts']['skip'],
                "s were" if self._process['counts']['skip'] != 1
                else " was",
            )
            if self._process['counts']['skip']
            else "During processing, "
        ]

        if self._process['counts']['fail']:
            if self._process['counts']['okay']:
                messages.append(
                    "%d note%s successfully updated, but "
                    "%d note%s failed while processing." % (
                        self._process['counts']['okay'],
                        "s were" if self._process['counts']['okay'] != 1
                        else " was",
                        self._process['counts']['fail'],
                        "s" if self._process['counts']['fail'] != 1
                        else "",
                    )
                )
            else:
                messages.append("no notes were successfully updated.")

            messages.append("\n\n")

            if len(self._process['exceptions']) == 1:
                messages.append("The following problem was encountered:")
                messages += [
                    "\n%s (%d time%s)" %
                    (message, count, "s" if count != 1 else "")
                    for message, count
                    in self._process['exceptions'].items()
                ]
            else:
                messages.append("The following problems were encountered:")
                messages += [
                    "\n- %s (%d time%s)" %
                    (message, count, "s" if count != 1 else "")
                    for message, count
                    in self._process['exceptions'].items()
                ]

        else:
            messages.append("there were no errors.")

        self._disable_inputs(False)
        self._alerts("".join(messages), self)
        self._notes = None
        self._process = None
        self._addon.config.update(self._remember_values())

        super(BrowserGenerator, self).accept()

    def _remember_values(self):

        source, dest, append, behavior = self._get_field_values()

        return dict(
            super(BrowserGenerator, self)._remember_values().items() +
            [
                ('last_mass_append', append),
                ('last_mass_behavior', behavior),
                ('last_mass_dest', dest),
                ('last_mass_source', source),
            ]
        )


    def _get_field_values(self):
        """
        Returns the user's source and destination fields, append state,
        and handling mode.
        """

        return (
            self.findChild(QtGui.QComboBox, 'source').currentText(),
            self.findChild(QtGui.QComboBox, 'dest').currentText(),
            self.findChild(QtGui.QRadioButton, 'append').isChecked(),
            self.findChild(QtGui.QCheckBox, 'behavior').isChecked(),
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
        super(EditorGenerator, self).__init__(
            title="Add TTS Audio to Note",
            *args, **kwargs
        )

    # UI Construction ########################################################

    def _ui_control(self):
        """
        Replaces the superclass's version of this with a version that
        returns a "Preview and Record" header, larger text input area,
        and preview button on its own line.
        """

        header = QtGui.QLabel("Preview and Record")
        header.setFont(self._FONT_HEADER)

        intro = QtGui.QLabel(
            "This text will be inserted as a [sound] tag and then "
            "synchronized along with other media in your collection."
        )
        intro.setTextFormat(QtCore.Qt.PlainText)
        intro.setWordWrap(True)

        text = QtGui.QPlainTextEdit()
        text.setObjectName('text')
        text.setTabChangesFocus(True)

        button = QtGui.QPushButton("&Preview")
        button.setObjectName('preview')
        button.clicked.connect(self._on_preview)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(intro)
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

    def accept(self):
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
                    super(EditorGenerator, self).accept(),
                    self._editor.addMedia(path),
                ),
                fail=lambda exception: (
                    self._alerts(exception.message, self),
                    text_input.setFocus(),
                ),
            ),
        )

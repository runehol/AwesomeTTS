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
Configuration dialog
"""

__all__ = ['Configurator']

import os
import os.path

from PyQt4 import QtCore, QtGui

from .base import Dialog
from .common import key_event_combo, key_combo_desc

# all methods might need 'self' in the future, pylint:disable=R0201


class Configurator(Dialog):
    """
    Provides a dialog for configuring the add-on.
    """

    _PROPERTY_KEYS = [
        'automatic_answers', 'automatic_questions', 'debug_file',
        'debug_stdout', 'delay_answers_onthefly', 'delay_answers_stored_ours',
        'delay_answers_stored_theirs', 'delay_questions_onthefly',
        'delay_questions_stored_ours', 'delay_questions_stored_theirs',
        'lame_flags', 'launch_browser_generator', 'launch_browser_stripper',
        'launch_configurator', 'launch_editor_generator', 'launch_templater',
        'spec_note_strip', 'spec_note_ellipsize', 'spec_template_ellipsize',
        'spec_note_count', 'spec_note_count_wrap', 'spec_template_count',
        'spec_template_count_wrap', 'spec_template_strip',
        'strip_note_braces', 'strip_note_brackets', 'strip_note_parens',
        'strip_template_braces', 'strip_template_brackets',
        'strip_template_parens', 'sub_note_cloze', 'sub_template_cloze',
        'sul_note', 'sul_template', 'throttle_sleep', 'throttle_threshold',
        'tts_key_a', 'tts_key_q', 'updates_enabled',
    ]

    _PROPERTY_WIDGETS = (
        QtGui.QCheckBox, QtGui.QComboBox, QtGui.QLineEdit, QtGui.QPushButton,
        QtGui.QSpinBox, QtGui.QListView,
    )

    __slots__ = [
    ]

    def __init__(self, *args, **kwargs):
        super(Configurator, self).__init__(title="Configuration",
                                           *args, **kwargs)

    # UI Construction ########################################################

    def _ui(self):
        """
        Returns a vertical layout with the superclass's banner, our tab
        area, and a row of the superclass's cancel/OK buttons.
        """

        layout = super(Configurator, self)._ui()
        layout.addWidget(self._ui_tabs())
        layout.addWidget(self._ui_buttons())

        return layout

    def _ui_tabs(self):
        """
        Returns a tab widget populated with four tabs: Playback, Text,
        MP3s, and Advanced.
        """

        tabs = QtGui.QTabWidget()

        # icons do not display correctly on Mac OS X when tab is active
        from sys import platform
        use_icons = not platform.startswith('darwin')

        for content, icon, label in [
                (self._ui_tabs_playback, 'player-time', "Playback"),
                (self._ui_tabs_text, 'editclear', "Text"),
                (self._ui_tabs_mp3gen, 'document-new', "MP3s"),
                (self._ui_tabs_windows, 'kpersonalizer', "Windows"),
                (self._ui_tabs_advanced, 'configure', "Advanced"),
        ]:
            if use_icons:
                tabs.addTab(
                    content(),
                    QtGui.QIcon(':/icons/%s.png' % icon),
                    label,
                )
            else:
                tabs.addTab(content(), label)

        tabs.currentChanged.connect(lambda: (
            tabs.adjustSize(),
            self.adjustSize(),
        ))

        return tabs

    def _ui_tabs_playback(self):
        """
        Returns the "Playback" tab.
        """

        notes = QtGui.QLabel('Anki controls if and how to play [sound] '
                             'tags. Click "Help" for more information.')

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._ui_tabs_playback_group(
            'automatic_questions',
            'tts_key_q',
            'delay_questions_',
            "Questions / Fronts of Cards",
        ))
        layout.addWidget(self._ui_tabs_playback_group(
            'automatic_answers',
            'tts_key_a',
            'delay_answers_',
            "Answers / Backs of Cards",
        ))
        layout.addSpacing(self._SPACING)
        layout.addWidget(notes)
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _ui_tabs_playback_group(self, automatic_key, shortcut_key,
                                delay_key_prefix, label):
        """
        Returns the "Questions / Fronts of Cards" and "Answers / Backs
        of Cards" input groups.
        """

        automatic = QtGui.QCheckBox("Automatically play on-the-fly <tts> tags")
        automatic.setObjectName(automatic_key)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(automatic)

        wait_widgets = {}

        for subkey, description in [
                ('onthefly', "on-the-fly <tts> tags"),
                ('stored_ours', "AwesomeTTS [sound] tags"),
                ('stored_theirs', "other [sound] tags"),
        ]:
            spinner = QtGui.QSpinBox()
            spinner.setObjectName(delay_key_prefix + subkey)
            spinner.setRange(0, 30)
            spinner.setSingleStep(1)
            spinner.setSuffix(" seconds")
            wait_widgets[subkey] = spinner

            horizontal = QtGui.QHBoxLayout()
            horizontal.addWidget(QtGui.QLabel("Wait"))
            horizontal.addWidget(spinner)
            horizontal.addWidget(QtGui.QLabel("before automatically "
                                              "playing " + description))
            horizontal.addStretch()

            layout.addLayout(horizontal)

        automatic.stateChanged.connect(wait_widgets['onthefly'].setEnabled)

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(QtGui.QLabel("To manually play on-the-fly <tts> "
                                          "tags, strike"))
        horizontal.addWidget(self._factory_shortcut(shortcut_key))
        horizontal.addStretch()

        layout.addLayout(horizontal)

        group = QtGui.QGroupBox(label)
        group.setLayout(layout)

        return group

    def _ui_tabs_text(self):
        """
        Returns the "Text" tab.
        """

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._ui_tabs_text_mode(
            '_template_',
            "Handling Template Text (e.g. On-the-Fly)",
            "For a front-side rendered cloze,",
            [
                ('anki', "read however Anki displayed it"),
                ('wrap', "read w/ hint wrapped in ellipses"),
                ('ellipsize', "read as an ellipsis, ignoring hint"),
                ('remove', "remove entirely"),
            ],
        ))
        layout.addWidget(self._ui_tabs_text_mode(
            '_note_',
            "Handling Text from a Note Field (e.g. Browser Generator)",
            "For a braced cloze marker,",
            [
                ('anki', "read as Anki would display on a card front"),
                ('wrap', "replace w/ hint wrapped in ellipses"),
                ('deleted', "replace w/ deleted text"),
                ('ellipsize', "replace w/ ellipsis, ignoring both"),
                ('remove', "remove entirely"),
            ],
        ))
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _ui_tabs_text_mode(self, infix, label, cloze_description,
                           cloze_options):
        """
        Returns a group box widget for the given text manipulation
        context.
        """

        subtabs = QtGui.QTabWidget()
        subtabs.setTabPosition(QtGui.QTabWidget.West)

        for sublabel, sublayout in [
                ("Simple", self._ui_tabs_text_mode_simple(infix,
                                                          cloze_description,
                                                          cloze_options)),
                ("Advanced", self._ui_tabs_text_mode_adv(infix)),
        ]:
            subwidget = QtGui.QWidget()
            subwidget.setLayout(sublayout)

            subtabs.addTab(subwidget, sublabel)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(subtabs)

        group = QtGui.QGroupBox(label)
        group.setLayout(layout)

        _, top, right, bottom = layout.getContentsMargins()
        layout.setContentsMargins(0, top, right, bottom)

        _, top, right, bottom = group.getContentsMargins()
        group.setContentsMargins(0, top, right, bottom)

        return group

    def _ui_tabs_text_mode_simple(self, infix, cloze_description,
                                  cloze_options):
        """
        Returns a layout with the "simple" configuration options
        available for manipulating text from the given context.
        """

        select = QtGui.QComboBox()
        for option_value, option_text in cloze_options:
            select.addItem(option_text, option_value)
        select.setObjectName(infix.join(['sub', 'cloze']))

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(QtGui.QLabel(cloze_description))
        horizontal.addWidget(select)
        horizontal.addStretch()

        layout = QtGui.QVBoxLayout()
        layout.addLayout(horizontal)

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(QtGui.QLabel("Strip off text within:"))

        for option_subkey, option_label in [('parens', "parentheses"),
                                            ('brackets', "brackets"),
                                            ('braces', "braces")]:
            checkbox = QtGui.QCheckBox(option_label)
            checkbox.setObjectName(infix.join(['strip', option_subkey]))
            horizontal.addWidget(checkbox)

        horizontal.addStretch()
        layout.addLayout(horizontal)

        layout.addLayout(self._ui_tabs_text_mode_simple_spec(
            infix,
            'strip',
            ("Remove all", "characters from the input"),
        ))
        layout.addLayout(self._ui_tabs_text_mode_simple_spec(
            infix,
            'count',
            ("Count adjacent", "characters"),
            True,
        ))
        layout.addLayout(self._ui_tabs_text_mode_simple_spec(
            infix,
            'ellipsize',
            ("Replace", "characters with an ellipsis"),
        ))

        layout.addStretch()

        return layout

    def _ui_tabs_text_mode_simple_spec(self, infix, suffix, labels,
                                       wrap=False):
        """Returns a layout for specific character handling."""

        line_edit = QtGui.QLineEdit()
        line_edit.setObjectName(infix.join(['spec', suffix]))
        line_edit.setValidator(self._ui_tabs_text_mode_simple_spec.ucsv)
        line_edit.setFixedWidth(50)

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(QtGui.QLabel(labels[0]))
        horizontal.addWidget(line_edit)
        horizontal.addWidget(QtGui.QLabel(labels[1]))

        if wrap:
            checkbox = QtGui.QCheckBox("wrap in ellipses")
            checkbox.setObjectName(''.join(['spec', infix, suffix, '_wrap']))
            horizontal.addWidget(checkbox)

        horizontal.addStretch()

        return horizontal

    class _UniqueCharacterStringValidator(QtGui.QValidator):
        """
        Provides a QValidator-compliant class that returns a string of
        unique, sorted characters containing no whitespace.
        """

        def fixup(self, original):
            """Returns unique characters from original, sorted."""

            return ''.join(sorted({c for c in original if not c.isspace()}))

        def validate(self, original, offset):  # pylint:disable=W0613
            """Fixes original text and resets cursor to end of line."""

            filtered = self.fixup(original)
            return QtGui.QValidator.Acceptable, filtered, len(filtered)

    _ui_tabs_text_mode_simple_spec.ucsv = _UniqueCharacterStringValidator()

    def _ui_tabs_text_mode_adv(self, infix):
        """
        Returns a layout with the "advanced" pattern replacement
        panel for manipulating text from the given context.
        """

        list_view = _SubListView()
        list_view.setObjectName('sul' + infix.rstrip('_'))

        add_btn = QtGui.QPushButton(QtGui.QIcon(':/icons/list-add.png'), "")
        add_btn.setIconSize(QtCore.QSize(16, 16))
        add_btn.setFlat(True)

        del_btn = QtGui.QPushButton(QtGui.QIcon(':/icons/editdelete.png'), "")
        del_btn.setIconSize(QtCore.QSize(16, 16))
        del_btn.setFlat(True)

        vertical = QtGui.QVBoxLayout()
        vertical.addWidget(add_btn)
        vertical.addWidget(del_btn)
        vertical.addStretch()

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(list_view)
        horizontal.addLayout(vertical)

        return horizontal

    def _ui_tabs_mp3gen(self):
        """
        Returns the "MP3s" tab.
        """

        notes = QtGui.QLabel(
            "As of Beta 11, AwesomeTTS will no longer generate filenames "
            "directly from input phrases. Instead, filenames will be based "
            "on a hash of the selected service, options, and phrase. This "
            "change should ensure unique and portable filenames.",
        )
        notes.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(notes)
        layout.addSpacing(self._SPACING)
        layout.addWidget(self._ui_tabs_mp3gen_lame())
        layout.addWidget(self._ui_tabs_mp3gen_throttle())
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _ui_tabs_mp3gen_lame(self):
        """
        Returns the "LAME Transcoder" input group.
        """

        notes = QtGui.QLabel("Specify flags passed to lame when making MP3s.")
        notes.setWordWrap(True)

        flags = QtGui.QLineEdit()
        flags.setObjectName('lame_flags')
        flags.setPlaceholderText("e.g. '-q 5' for medium quality")

        addl = QtGui.QLabel(
            "Affects %s. Changes will NOT be retroactive to old MP3s. "
            "Depending on the change, you may want to regenerate MP3s and/or "
            "clear your cache on the Advanced tab. Edit with caution." %
            ', '.join(self._addon.router.by_trait(
                self._addon.router.Trait.TRANSCODING,
            ))
        )
        addl.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(notes)
        layout.addWidget(flags)
        layout.addWidget(addl)

        group = QtGui.QGroupBox("LAME Transcoder")
        group.setLayout(layout)

        return group

    def _ui_tabs_mp3gen_throttle(self):
        """
        Returns the "Download Throttling" input group.
        """

        notes = QtGui.QLabel(
            "Tweak how often AwesomeTTS takes a break when downloading files "
            "from online services in a batch (e.g. from the card browser)."
        )
        notes.setWordWrap(True)

        threshold_label = QtGui.QLabel("After downloading ")

        threshold = QtGui.QSpinBox()
        threshold.setObjectName('throttle_threshold')
        threshold.setRange(5, 1000)
        threshold.setSingleStep(5)
        threshold.setSuffix(" files")

        sleep_label = QtGui.QLabel(" sleep for ")

        sleep = QtGui.QSpinBox()
        sleep.setObjectName('throttle_sleep')
        sleep.setRange(15, 10800)
        sleep.setSingleStep(15)
        sleep.setSuffix(" seconds")

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(threshold_label)
        horizontal.addWidget(threshold)
        horizontal.addWidget(sleep_label)
        horizontal.addWidget(sleep)
        horizontal.addStretch()

        addl = QtGui.QLabel(
            "Affects %s." %
            ', '.join(self._addon.router.by_trait(
                self._addon.router.Trait.INTERNET,
            ))
        )
        addl.setWordWrap(True)

        vertical = QtGui.QVBoxLayout()
        vertical.addWidget(notes)
        vertical.addLayout(horizontal)
        vertical.addWidget(addl)

        group = QtGui.QGroupBox("Download Throttling during Batch Processing")
        group.setLayout(vertical)

        return group

    def _ui_tabs_windows(self):
        """
        Returns the "Window" tab.
        """

        grid = QtGui.QGridLayout()
        for i, (desc, sub) in enumerate([
                ("open configuration in main window", 'configurator'),
                ("insert <tts> tag in template editor", 'templater'),
                ("mass generate MP3s in card browser", 'browser_generator'),
                ("mass remove audio in card browser", 'browser_stripper'),
                ("generate single MP3 in note editor*", 'editor_generator'),
        ]):
            grid.addWidget(QtGui.QLabel("To " + desc + ", strike"), i, 0)
            grid.addWidget(self._factory_shortcut('launch_' + sub), i, 1)
        grid.setColumnStretch(1, 1)

        group = QtGui.QGroupBox("Window Shortcuts")
        group.setLayout(grid)

        note = QtGui.QLabel(
            "* By default, AwesomeTTS binds %(native)s for most actions. "
            "However, if you use math equations and LaTeX with Anki using "
            "the %(native)s E/M/T keystrokes, you may want to reassign or "
            "unbind the shortcut for generating MP3s in the note editor." %
            dict(native=key_combo_desc(QtCore.Qt.ControlModifier |
                                       QtCore.Qt.Key_T))
        )
        note.setWordWrap(True)

        disclaimer = QtGui.QLabel(
            "Changes to editor and browser shortcuts will take effect the "
            "next time you open those windows."
        )
        disclaimer.setWordWrap(True)

        disclaimer2 = QtGui.QLabel(
            "Some keys cannot be used as shortcuts. Additionally, certain "
            "keystrokes might not work in certain windows depending on your "
            "operating system and other add-ons you are running, so you may "
            "have to experiment to find what works best."
        )
        disclaimer2.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(group)
        layout.addWidget(note)
        layout.addWidget(disclaimer)
        layout.addWidget(disclaimer2)
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _ui_tabs_advanced(self):
        """
        Returns the "Advanced" tab.
        """

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._ui_tabs_advanced_update())
        layout.addWidget(self._ui_tabs_advanced_debug())
        layout.addWidget(self._ui_tabs_advanced_cache())
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _ui_tabs_advanced_update(self):
        """
        Returns the "Updates" input group.
        """

        updates = QtGui.QCheckBox(
            "automatically check for AwesomeTTS updates at start-up"
        )
        updates.setObjectName('updates_enabled')

        button = QtGui.QPushButton(
            QtGui.QIcon(':/icons/find.png'),
            "Check Now",
        )
        button.setSizePolicy(
            QtGui.QSizePolicy.Fixed,
            QtGui.QSizePolicy.Fixed,
        )
        button.setObjectName('updates_button')
        button.clicked.connect(self._on_update_request)

        state = QtGui.QLabel()
        state.setObjectName('updates_state')
        state.setTextFormat(QtCore.Qt.PlainText)
        state.setWordWrap(True)

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(button)
        horizontal.addWidget(state)

        vertical = QtGui.QVBoxLayout()
        vertical.addWidget(updates)
        vertical.addLayout(horizontal)

        group = QtGui.QGroupBox("Updates")
        group.setLayout(vertical)

        return group

    def _ui_tabs_advanced_debug(self):
        """
        Returns the "Write Debugging Output" input group.
        """

        stdout = QtGui.QCheckBox("standard output (stdout)")
        stdout.setObjectName('debug_stdout')

        log = QtGui.QCheckBox("log file in add-on directory")
        log.setObjectName('debug_file')

        layout = QtGui.QVBoxLayout()
        layout.addWidget(stdout)
        layout.addWidget(log)

        group = QtGui.QGroupBox("Write Debugging Output")
        group.setLayout(layout)

        return group

    def _ui_tabs_advanced_cache(self):
        """
        Returns the "Media Cache" input group.
        """

        button = QtGui.QPushButton("Clear Cache")
        button.setObjectName('on_cache')
        button.clicked.connect(lambda: self._on_cache_clear(button))

        notes = QtGui.QLabel(
            "Media files are cached locally for successive playback and "
            "recording requests. The cache improves performance of the "
            "add-on, particularly when using the on-the-fly mode, but you "
            "may want to clear it from time to time."
        )
        notes.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(button)
        layout.addWidget(notes)

        group = QtGui.QGroupBox("Media Cache")
        group.setLayout(layout)

        return group

    # Factories ##############################################################

    def _factory_shortcut(self, object_name):
        """Returns a push button capable of being assigned a shortcut."""

        shortcut = QtGui.QPushButton()
        shortcut.awesometts_pending = False
        shortcut.setObjectName(object_name)
        shortcut.setCheckable(True)
        shortcut.toggled.connect(
            lambda is_down: (
                shortcut.setText("press keystroke"),
                shortcut.setFocus(),  # needed for OS X if text inputs present
            ) if is_down
            else shortcut.setText(key_combo_desc(shortcut.awesometts_value))
        )

        return shortcut

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Restores state on all form inputs. This should be roughly the
        opposite of the accept() method.
        """

        for widget, value in [
                (widget, self._addon.config[widget.objectName()])
                for widget in self.findChildren(self._PROPERTY_WIDGETS)
                if widget.objectName() in self._PROPERTY_KEYS
        ]:
            if isinstance(widget, QtGui.QCheckBox):
                widget.setChecked(value)
                widget.stateChanged.emit(value)

            elif isinstance(widget, QtGui.QLineEdit):
                widget.setText(value)

            elif isinstance(widget, QtGui.QPushButton):
                widget.awesometts_value = value
                widget.setText(key_combo_desc(widget.awesometts_value))

            elif isinstance(widget, QtGui.QComboBox):
                widget.setCurrentIndex(max(widget.findData(value), 0))

            elif isinstance(widget, QtGui.QSpinBox):
                widget.setValue(value)

            elif isinstance(widget, QtGui.QListView):
                widget.setModel(value)

        widget = self.findChild(QtGui.QPushButton, 'on_cache')
        if widget:
            widget.awesometts_list = (
                [filename for filename in os.listdir(self._addon.paths.cache)]
                if os.path.isdir(self._addon.paths.cache)
                else []
            )

            if len(widget.awesometts_list):
                import locale

                widget.setEnabled(True)
                widget.setText(
                    "Clear Cache (%s item%s)" % (
                        locale.format(
                            "%d",
                            len(widget.awesometts_list),
                            grouping=True,
                        ),
                        "" if len(widget.awesometts_list) == 1 else "s",
                    )
                )

            else:
                widget.setEnabled(False)
                widget.setText("Clear Cache (no items)")

        super(Configurator, self).show(*args, **kwargs)

    def accept(self):
        """
        Saves state on all form inputs. This should be roughly the
        opposite of the show() method.

        Once done, we pass the signal onto Qt to close the window.
        """

        self._addon.config.update({
            widget.objectName(): (
                widget.isChecked() if isinstance(
                    widget,
                    QtGui.QCheckBox,
                )
                else widget.awesometts_value if isinstance(
                    widget,
                    QtGui.QPushButton,
                )
                else widget.value() if isinstance(
                    widget,
                    QtGui.QSpinBox,
                )
                else widget.itemData(widget.currentIndex()) if isinstance(
                    widget,
                    QtGui.QComboBox,
                )
                else widget.model().raw_data if isinstance(
                    widget,
                    QtGui.QListView,
                )
                else widget.text()
            )
            for widget in self.findChildren(self._PROPERTY_WIDGETS)
            if widget.objectName() in self._PROPERTY_KEYS
        })

        super(Configurator, self).accept()

    def help_request(self):
        """
        Launch the web browser with the URL to the documentation for the
        user's current tab.
        """

        tabs = self.findChild(QtGui.QTabWidget)
        self._launch_link(
            'config/' +
            tabs.tabText(tabs.currentIndex()).lower()
        )

    def keyPressEvent(self, key_event):  # from PyQt4, pylint:disable=C0103
        """Assign new combo for shortcut buttons undergoing changes."""

        buttons = self._get_pressed_shortcut_buttons()
        if not buttons:
            return super(Configurator, self).keyPressEvent(key_event)

        key = key_event.key()

        if key == QtCore.Qt.Key_Escape:
            for button in buttons:
                button.awesometts_pending = False
                button.setText(key_combo_desc(button.awesometts_value))
            return

        if key in [QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete]:
            combo = None

        else:
            combo = key_event_combo(key_event)
            if not combo:
                return

        for button in buttons:
            button.awesometts_pending = combo
            button.setText(key_combo_desc(combo))

    def keyReleaseEvent(self, key_event):  # from PyQt4, pylint:disable=C0103
        """Disengage all shortcut buttons undergoing changes."""

        buttons = self._get_pressed_shortcut_buttons()

        if not buttons:
            return super(Configurator, self).keyReleaseEvent(key_event)

        elif key_event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            # need to ignore and eat key release on enter/return so that user
            # can activate the button without immediately deactivating it
            return

        for button in buttons:
            if button.awesometts_pending is not False:
                button.awesometts_value = button.awesometts_pending
            button.setChecked(False)

    def _get_pressed_shortcut_buttons(self):
        """Returns all shortcut buttons that are pressed."""

        return [button
                for button in self.findChildren(QtGui.QPushButton)
                if (button.isChecked() and
                    (button.objectName().startswith('launch_') or
                     button.objectName().startswith('tts_key_')))]

    def _on_update_request(self):
        """
        Attempts the update request using the lower level update object.
        """

        button = self.findChild(QtGui.QPushButton, 'updates_button')
        state = self.findChild(QtGui.QLabel, 'updates_state')

        button.setEnabled(False)
        state.setText("Querying update server...")

        from . import Updater
        self._addon.updates.check(
            callbacks=dict(
                done=lambda: button.setEnabled(True),
                fail=lambda exception: state.setText(
                    "Check unsuccessful: %s" % (
                        exception.message or
                        format(exception) or
                        "Nothing further known"
                    )
                ),
                good=lambda: state.setText("No update needed at this time."),
                need=lambda version, info: (
                    state.setText("Update to %s is available" % version),
                    [
                        updater.show()
                        for updater in [Updater(
                            version=version,
                            info=info,
                            is_manual=True,
                            addon=self._addon,
                            parent=(
                                self if self.isVisible()
                                else self.parentWidget()
                            ),
                        )]
                    ],
                ),
            ),
        )

    def _on_cache_clear(self, button):
        """
        Attempts to delete all the files in the cache directory, as they
        were reported when the modal was opened.
        """

        button.setEnabled(False)

        count_success = 0
        count_error = 0

        for filename in button.awesometts_list:
            try:
                os.unlink(os.path.join(self._addon.paths.cache, filename))
                count_success += 1
            except:  # capture all exceptions, pylint:disable=W0702
                count_error += 1

        if count_error:
            if count_success:
                import locale
                button.setText(
                    "partially emptied cache (%s item%s remaining)" % (
                        locale.format("%d", count_error, grouping=True),
                        "" if count_error == 1 else "s",
                    )
                )

            else:
                button.setText("unable to empty cache")

        else:
            button.setText("successfully emptied cache")


class _SubRuleDelegate(QtGui.QItemDelegate):
    """Item view specifically for a substitution rule."""

    sizeHint = lambda self, option, index: self.sizeHint.SIZE
    sizeHint.SIZE = QtCore.QSize(-1, 50)

    def createEditor(self, parent,    # pylint:disable=C0103
                     option, index):  # pylint:disable=W0613
        """Return a panel to change rule values."""

        edits = QtGui.QHBoxLayout()
        edits.addWidget(QtGui.QLineEdit())
        edits.addWidget(QtGui.QLabel("<strong>&rArr;</strong>"))
        edits.addWidget(QtGui.QLineEdit())
        edits.setContentsMargins(0, 0, 0, 0)

        checkboxes = QtGui.QHBoxLayout()
        checkboxes.addWidget(QtGui.QCheckBox("regex"))
        checkboxes.addWidget(QtGui.QCheckBox("case-insensitive"))
        checkboxes.addWidget(QtGui.QCheckBox("unicode"))
        checkboxes.addStretch()
        checkboxes.setContentsMargins(0, 0, 0, 0)

        layout = QtGui.QVBoxLayout()
        layout.addStretch()
        layout.addLayout(edits)
        layout.addLayout(checkboxes)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)

        panel = QtGui.QWidget(parent)
        panel.setAutoFillBackground(True)
        panel.setFocusPolicy(QtCore.Qt.StrongFocus)
        panel.setLayout(layout)
        panel.setContentsMargins(0, 0, 0, 0)

        return panel

    def setEditorData(self, editor, index):  # pylint:disable=C0103
        """Populate controls and focus the first edit box."""

        rule = index.data(QtCore.Qt.EditRole)

        edits = editor.findChildren(QtGui.QLineEdit)
        edits[0].setText(rule['input'])
        edits[1].setText(rule['replace'])

        checkboxes = editor.findChildren(QtGui.QCheckBox)
        checkboxes[0].setChecked(rule['regex'])
        checkboxes[1].setChecked(rule['ignore_case'])
        checkboxes[2].setChecked(rule['unicode'])

        QtCore.QTimer.singleShot(0, edits[0].setFocus)

    def setModelData(self, editor, model, index):  # pylint:disable=C0103
        """Update the underlying model after edit."""

        edits = editor.findChildren(QtGui.QLineEdit)
        checkboxes = editor.findChildren(QtGui.QCheckBox)

        # TODO should validation/compilation happen here or in setData()?
        model.setData(index, {
            'input': edits[0].text(),  # TODO this needs validation
            'replace': edits[1].text(),
            'regex': checkboxes[0].isChecked(),
            'ignore_case': checkboxes[1].isChecked(),
            'unicode': checkboxes[2].isChecked(),
            # TODO 'compiled': ...
        })


class _SubListView(QtGui.QListView):
    """List view specifically for substitution lists."""

    setModel = lambda self, model: \
        super(_SubListView, self).setModel(_SubListModel(model))

    def __init__(self, *args, **kwargs):
        super(_SubListView, self).__init__(*args, **kwargs)
        self.setItemDelegate(self.__init__.DELEGATE)
    __init__.DELEGATE = _SubRuleDelegate()


class _SubListModel(QtCore.QAbstractListModel):  # pylint:disable=R0904
    """Provides glue to/from the underlying substitution list."""

    __slots__ = ['raw_data']

    flags = lambda self, index: self.flags.LIST_ITEM
    flags.LIST_ITEM = (QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable |
                       QtCore.Qt.ItemIsEnabled)

    rowCount = lambda self, parent: len(self.raw_data)

    def __init__(self, sublist, *args, **kwargs):
        super(_SubListModel, self).__init__(*args, **kwargs)
        self.raw_data = [dict(obj) for obj in sublist]  # deep copy

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Return display or edit data for the indexed rule."""

        if role == QtCore.Qt.DisplayRole:
            rule = self.raw_data[index.row()]
            text = ('/%s/' if rule['regex'] else '"%s"') % rule['input']
            action = ('replace it with "%s"' % rule['replace']
                      if rule['replace'] else "remove it")
            attr = ", ".join([
                "regex pattern" if rule['regex'] else "plain text",
                "case-insensitive" if rule['ignore_case'] else "case matters",
                "unicode enabled" if rule['unicode'] else "unicode disabled",
            ])

            return "match " + text + " and " + action + "\n(" + attr + ")"

        elif role == QtCore.Qt.EditRole:
            return self.raw_data[index.row()]

    def setData(self, index, value,        # pylint:disable=C0103
                role=QtCore.Qt.EditRole):  # pylint:disable=W0613
        """Update the new value into the raw list."""

        self.raw_data[index.row()] = value
        return True

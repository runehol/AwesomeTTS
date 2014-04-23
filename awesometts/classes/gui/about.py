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
About dialog and associated GUI elements
"""

__all__ = ['Action', 'Dialog']

import os, os.path
from PyQt4 import QtCore, QtGui

# all methods might need 'self' in the future, pylint:disable=R0201


class Action(QtGui.QAction):
    """
    Provides an "AwesomeTTS" menu action to trigger another window.
    """

    __slots__ = []

    def __init__(self, main_window, triggered_window):
        """
        Initializes the menu action, wires its 'triggered' event, and
        adds it to the Tools menu via Anki's API.
        """

        super(Action, self).__init__(
            QtGui.QIcon(':/icons/speaker.png'),  # if enabled in DE
            "A&wesomeTTS",
            main_window,
        )

        self.triggered.connect(
            # passed event must be discarded, pylint:disable=W0108
            lambda: triggered_window.show()
        )

        main_window.form.menuTools.addAction(self)


class Dialog(QtGui.QDialog):
    """
    Provides a dialog for configuring the add-on.
    """

    __slots__ = [
        '_cache_dir',  # path to the cache directory
        '_conf',       # dict-like configuration object
        '_qt_keys',    # mapping of QT key integers to human-readable names
        '_router',     # add-on router for resolving traits
        '_setup',      # True if the UI has been built out, False otherwise
        '_version',    # current version of the add-on
    ]

    def __init__(self, main_window, environ, version):

        super(Dialog, self).__init__(main_window)

        self._cache_dir = environ['cache_dir']
        self._conf = environ['conf']
        self._qt_keys = None  # built when UI first shown in show() below
        self._router = environ['router']
        self._setup = False
        self._version = version

    # Events #################################################################


    _PROPERTY_KEYS = [
        'automatic_answers', 'automatic_questions', 'debug_file',
        'debug_stdout', 'lame_flags', 'throttle_sleep', 'throttle_threshold',
        'tts_key_a', 'tts_key_q',
    ]

    _PROPERTY_WIDGETS = (
        QtGui.QCheckBox, QtGui.QLineEdit, QtGui.QPushButton, QtGui.QSpinBox,
    )

    def show(self, *args, **kwargs):
        """
        Checks to see if the UI has been built out and restores state on
        all form inputs. This should be roughly the opposite of the
        accept() method.
        """

        if not self._setup:
            self._build_ui()

        for widget, value in [
            (widget, self._conf[widget.objectName()])
            for widget in self.findChildren(self._PROPERTY_WIDGETS)
            if widget.objectName() in self._PROPERTY_KEYS
        ]:
            if isinstance(widget, QtGui.QCheckBox):
                widget.setChecked(value)

            elif isinstance(widget, QtGui.QLineEdit):
                widget.setText(value)

            elif isinstance(widget, QtGui.QPushButton):
                widget.awesometts_value = value
                widget.setText(
                    "Change Shortcut (currently %s)" %
                    self._get_key(widget.awesometts_value),
                )

            elif isinstance(widget, QtGui.QSpinBox):
                widget.setValue(value)

        widget = self.findChild(QtGui.QPushButton, 'on_cache')
        if widget:
            widget.awesometts_list = (
                [filename for filename in os.listdir(self._cache_dir)]
                if os.path.isdir(self._cache_dir)
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

        super(Dialog, self).show(*args, **kwargs)

    def accept(self, *args, **kwargs):
        """
        Saves state on all form inputs. This should be roughly the
        opposite of the show() method.
        """

        self._conf.update({
            widget.objectName(): (
                widget.isChecked() if isinstance(widget, QtGui.QCheckBox)
                else widget.awesometts_value if
                    isinstance(widget, QtGui.QPushButton)
                else widget.value() if isinstance(widget, QtGui.QSpinBox)
                else widget.text()
            )
            for widget in self.findChildren(self._PROPERTY_WIDGETS)
            if widget.objectName() in self._PROPERTY_KEYS
        })

        super(Dialog, self).accept(*args, **kwargs)

    def keyPressEvent(self, key_event):  # from PyQt4, pylint:disable=C0103
        """
        If we have a shortcut button awaiting a key event to change its
        binding, we capture it and process it.

        Otherwise, we forward to the superclass.
        """

        buttons = [
            button
            for button in self.findChildren(QtGui.QPushButton)
            if button.objectName().startswith('tts_key_') and
                button.isChecked()
        ]

        if not buttons:
            return super(Dialog, self).keyPressEvent(key_event)

        new_value = (
            None if key_event.key() in [
                QtCore.Qt.Key_Escape,
                QtCore.Qt.Key_Backspace,
                QtCore.Qt.Key_Delete,
            ]
            else key_event.key()
        )

        for button in buttons:
            button.awesometts_value = new_value
            button.setChecked(False)
            button.setText(
                "Change Shortcut (now %s)" %
                self._get_key(button.awesometts_value),
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
                os.unlink(os.path.join(self._cache_dir, filename))
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

    # UI Construction ########################################################

    def _build_ui(self):
        """
        Initializes the key look, titles the window, sets its layout,
        and marks the object as "_setup".
        """

        self._qt_keys = {
            value: key[4:]
            for key, value
            in vars(QtCore.Qt).items()
            if len(key) > 4 and key.startswith('Key_')
        }

        self.setModal(True)
        self.setWindowTitle("AwesomeTTS")
        self.setLayout(self._create())

        self._setup = True

    def _create(self):
        """
        Returns a vertical layout with a banner, tab area, and row of
        cancel/OK buttons.
        """

        layout = QtGui.QVBoxLayout()

        layout.addLayout(self._create_banner())
        layout.addWidget(self._create_tabs())
        layout.addWidget(self._create_buttons())

        return layout

    def _create_banner(self):
        """
        Returns a horizontal layout with some title text, a strecher,
        and version text.
        """

        name = QtGui.QLabel("AwesomeTTS")
        name_font = QtGui.QFont()
        name_font.setPointSize(20)
        name_font.setBold(True)
        name.setFont(name_font)

        version = QtGui.QLabel(self._version)
        version_font = QtGui.QFont()
        version_font.setItalic(True)
        version.setFont(version_font)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(version)

        return layout

    def _create_tabs(self):
        """
        Returns a tab widget populated with three tabs: On-the-Fly Mode,
        MP3 Generation, and Advanced.
        """

        tabs = QtGui.QTabWidget()

        tabs.addTab(
            self._create_tabs_onthefly(),
            QtGui.QIcon(':/icons/text-xml.png'),
            "On-the-Fly Mode",
        )

        tabs.addTab(
            self._create_tabs_mp3gen(),
            QtGui.QIcon(':/icons/document-new.png'),
            "MP3 Generation",
        )

        tabs.addTab(
            self._create_tabs_advanced(),
            QtGui.QIcon(':/icons/configure.png'),
            "Advanced",
        )

        return tabs

    def _create_tabs_onthefly(self):
        """
        Returns the "On-the-Fly Mode" tab.
        """

        intro = QtGui.QLabel("Control how <tts> template tags are played.")

        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro)
        layout.addSpacing(10)
        layout.addWidget(self._create_tabs_onthefly_group(
            'automatic_questions',
            'tts_key_q',
            "Questions / Fronts of Cards",
        ))
        layout.addWidget(self._create_tabs_onthefly_group(
            'automatic_answers',
            'tts_key_a',
            "Answers / Backs of Cards",
        ))
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _create_tabs_onthefly_group(self, automatic_key, shortcut_key, label):
        """
        Returns the "Questions / Fronts of Cards" and "Answers / Backs
        of Cards" input groups.
        """

        automatic = QtGui.QCheckBox("Automatically recite <tts> tags")
        automatic.setObjectName(automatic_key)

        shortcut = QtGui.QPushButton("Change Shortcut")
        shortcut.setObjectName(shortcut_key)
        shortcut.setCheckable(True)
        shortcut.toggled.connect(
            lambda is_down: shortcut.setText(
                "press any key" if is_down
                else "Change Shortcut (left as %s)" %
                    self._get_key(shortcut.awesometts_value)
            )
        )

        layout = QtGui.QVBoxLayout()
        layout.addWidget(automatic)
        layout.addWidget(shortcut)

        group = QtGui.QGroupBox(label)
        group.setLayout(layout)

        return group

    def _create_tabs_mp3gen(self):
        """
        Returns the "MP3 Generation" tab.
        """

        intro = QtGui.QLabel("Control how MP3s are generated.")

        notes = QtGui.QLabel(
            "As of Beta 11, AwesomeTTS will no longer generate filenames "
            "directly from input phrases. Instead, filenames will be based "
            "on a hash of the selected service, options, and phrase. This "
            "change should ensure unique and portable filenames.",
        )
        notes.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro)
        layout.addWidget(notes)
        layout.addSpacing(10)
        layout.addWidget(self._create_tabs_mp3gen_lame())
        layout.addWidget(self._create_tabs_mp3gen_throttle())
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _create_tabs_mp3gen_lame(self):
        """
        Returns the "LAME Transcoder" input group.
        """

        notes = QtGui.QLabel(
            "Specify flags to be passed to lame when generating MP3s "
            "(affects %s). Edit with caution." %
            ', '.join(self._router.by_trait(self._router.Trait.TRANSCODING)),
        )
        notes.setWordWrap(True)

        flags = QtGui.QLineEdit()
        flags.setObjectName('lame_flags')
        flags.setPlaceholderText("e.g. '-q 5' for medium quality")

        addl = QtGui.QLabel(
            "Changes in these flags will be retroactive to old MP3s. "
            "Depending on the change, you may want to regenerate MP3s and/or "
            "clear your cache on the Advanced tab.",
        )
        addl.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(notes)
        layout.addWidget(flags)
        layout.addWidget(addl)

        group = QtGui.QGroupBox("LAME Transcoder")
        group.setLayout(layout)

        return group

    def _create_tabs_mp3gen_throttle(self):
        """
        Returns the "Download Throttling" input group.
        """

        notes = QtGui.QLabel(
            "Tweak how often AwesomeTTS takes a break when downloading files "
            "from online services (affects %s)." %
            ', '.join(self._router.by_trait(self._router.Trait.INTERNET)),
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

        vertical = QtGui.QVBoxLayout()
        vertical.addWidget(notes)
        vertical.addLayout(horizontal)

        group = QtGui.QGroupBox("Download Throttling")
        group.setLayout(vertical)

        return group

    def _create_tabs_advanced(self):
        """
        Returns the "Advanced" tab.
        """

        intro = QtGui.QLabel("Control debugging options and the media cache.")

        layout = QtGui.QVBoxLayout()
        layout.addWidget(intro)
        layout.addSpacing(10)
        layout.addWidget(self._create_tabs_advanced_debug())
        layout.addWidget(self._create_tabs_advanced_cache())
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)

        return tab

    def _create_tabs_advanced_debug(self):
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

    def _create_tabs_advanced_cache(self):
        """
        Returns the "Media Cache" input group.
        """

        notes = QtGui.QLabel(
            "Media files are cached locally for successive playback and "
            "recording requests. The cache improves performance of the "
            "add-on, particularly when using the on-the-fly mode, but you "
            "may want to clear it from time to time."
        )
        notes.setWordWrap(True)

        button = QtGui.QPushButton("Clear Cache")
        button.setObjectName('on_cache')
        button.clicked.connect(lambda: self._on_cache_clear(button))

        layout = QtGui.QVBoxLayout()
        layout.addWidget(notes)
        layout.addWidget(button)

        group = QtGui.QGroupBox("Media Cache")
        group.setLayout(layout)

        return group

    def _create_buttons(self):
        """
        Returns a horizontal row of cancel/OK buttons.
        """

        buttons = QtGui.QDialogButtonBox()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel |
            QtGui.QDialogButtonBox.Ok
        )

        return buttons

    # Auxiliary ##############################################################

    def _get_key(self, code):
        """
        Retrieve the human-readable version of the given Qt key code.
        """

        return self._qt_keys.get(code, 'unknown') if code else 'unassigned'

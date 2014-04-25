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
Base classes for GUI elements

Provides classes that can be extended for constructing GUI elements for
use with AwesomeTTS.
"""

__all__ = ['Dialog', 'ServiceDialog']

from PyQt4 import QtCore, QtGui
from .common import ICON

# all methods might need 'self' in the future, pylint:disable=R0201


class Dialog(QtGui.QDialog):
    """
    Base used for all dialog windows.
    """

    __slots__ = [
        '_addon',  # bundle of config, logger, paths, router, version
    ]

    def __init__(self, addon, parent):
        """
        Set the modal status for the dialog, sets its layout to the
        return value of the _ui() method, and sets a default title.
        """

        self._addon = addon
        self._addon.logger.debug(
            "Constructing %s dialog",
            self.__class__.__name__,
        )

        super(Dialog, self).__init__(parent)

        self.setModal(True)
        self.setLayout(self._ui())
        self.setWindowIcon(ICON)
        self.setWindowTitle("AwesomeTTS")

    # UI Construction ########################################################

    def _ui(self):
        """
        Returns a vertical layout with a banner.

        Subclasses should call this method first when overriding so that
        all dialogs have the same banner.
        """

        layout = QtGui.QVBoxLayout()
        layout.addLayout(self._ui_banner())

        return layout

    def _ui_banner(self):
        """
        Returns a horizontal layout with some title text, a strecher,
        and version text.

        For subclasses, this method will be called automatically as part
        of the base class _ui() method.
        """

        name = QtGui.QLabel("AwesomeTTS")
        name_font = QtGui.QFont()
        name_font.setPointSize(20)
        name_font.setBold(True)
        name.setFont(name_font)

        version = QtGui.QLabel(self._addon.version)
        version_font = QtGui.QFont()
        version_font.setItalic(True)
        version.setFont(version_font)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(version)

        return layout

    def _ui_buttons(self):
        """
        Returns a horizontal row of cancel/OK buttons.

        Subclasses must call this method explicitly, at a location of
        their choice. Once called, the 'accept' and 'reject' signals
        become available.
        """

        buttons = QtGui.QDialogButtonBox()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel |
            QtGui.QDialogButtonBox.Ok
        )

        return buttons

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Writes a log message and pass onto superclass.
        """

        self._addon.logger.debug("Showing '%s' dialog", self.windowTitle())
        super(Dialog, self).show(*args, **kwargs)


class ServiceDialog(Dialog):
    """
    Base used for all service-related dialog windows (e.g. single file
    generator, mass file generator, template tag builder).
    """

    __slots__ = [
        '_panel_ready'  # map of svc_ids to True if that service is ready
    ]

    def __init__(self, *args, **kwargs):
        """
        Initialize the mechanism for keeping track of which panels are
        loaded.
        """

        self._panel_ready = {}

        super(ServiceDialog, self).__init__(*args, **kwargs)

    # UI Construction ########################################################

    def _ui(self):
        """
        Return a services panel and a control panel.
        """

        layout = super(ServiceDialog, self)._ui()

        horizontal = QtGui.QHBoxLayout()
        horizontal.addLayout(self._ui_services())
        horizontal.addLayout(self._ui_control())

        layout.addLayout(horizontal)
        return layout

    def _ui_services(self):
        """
        Return the service panel, which includes a dropdown for the
        service and a stacked widget for each service's options.
        """

        intro = QtGui.QLabel("Generate using")

        dropdown = QtGui.QComboBox()
        dropdown.setObjectName('service')

        stack = QtGui.QStackedWidget()
        stack.setObjectName('panels')

        for svc_id, text in self._addon.router.get_services()['values']:
            dropdown.addItem(text, svc_id)

            label = QtGui.QLabel("Pass the following to %s:" % text)

            panel = QtGui.QGridLayout()
            panel.addWidget(label, 0, 0, 1, 2)

            widget = QtGui.QWidget()
            widget.setLayout(panel)

            stack.addWidget(widget)

        dropdown.activated.connect(self._on_service_activated)

        horizontal = QtGui.QHBoxLayout()
        horizontal.addWidget(intro)
        horizontal.addWidget(dropdown)
        horizontal.addStretch()

        layout = QtGui.QVBoxLayout()
        layout.addLayout(horizontal)
        layout.addWidget(stack)

        return layout

    def _ui_control(self):
        """
        Return the text input and a preview button.
        """

        layout = QtGui.QVBoxLayout()

        text = QtGui.QPlainTextEdit()
        text.setObjectName('text')

        button = QtGui.QPushButton("&Preview")
        button.setObjectName('preview')
        button.clicked.connect(self._on_preview)

        layout.addWidget(text)
        layout.addWidget(button)

        return layout

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Recall the last used (or default) service and call in to
        activate its panel.
        """

        svc_id = self._addon.router.get_services()['current']
        dropdown = self.findChild(QtGui.QComboBox, 'service')
        idx = dropdown.findData(svc_id)

        dropdown.setCurrentIndex(idx)
        self._on_service_activated(idx, svc_id)

        super(ServiceDialog, self).show(*args, **kwargs)

    def _on_service_activated(self, idx, svc_id=None):
        """
        Switch the stack widget to the given service, constructing the
        panel if it has not already been constructed.
        """

        if not svc_id:
            svc_id = self.findChild(QtGui.QComboBox, 'service').itemData(idx)
        stack = self.findChild(QtGui.QStackedWidget, 'panels')

        if svc_id not in self._panel_ready:
            self._panel_ready[svc_id] = True
            self._addon.logger.debug("Constructing panel for %s", svc_id)

            row = 1
            panel = stack.widget(idx).layout()

            font = QtGui.QFont()
            font.setBold(True)

            for option in self._addon.router.get_options(svc_id):
                label = QtGui.QLabel(option['label'])
                label.setFont(font)

                if isinstance(option['values'], tuple):
                    start, end = option['values'][0], option['values'][1]

                    vinput = (
                        QtGui.QDoubleSpinBox
                        if isinstance(start, float) or isinstance(end, float)
                        else QtGui.QSpinBox
                    )()

                    vinput.setRange(start, end)
                    if len(option['values']) > 2:
                        vinput.setSuffix(" " + option['values'][2])

                    vinput.setValue(option['current'])

                else:  # list of tuples
                    vinput = QtGui.QComboBox()
                    for value, text in option['values']:
                        vinput.addItem(text, value)

                    vinput.setCurrentIndex(vinput.findData(option['current']))

                panel.addWidget(label, row, 0)
                panel.addWidget(vinput, row, 1)

                row += 1

            font = QtGui.QFont()
            font.setItalic(True)

            label = QtGui.QLabel(self._addon.router.get_desc(svc_id))
            label.setWordWrap(True)
            label.setFont(font)

            panel.addWidget(label, row, 0, 1, 2, QtCore.Qt.AlignBottom)
            panel.setRowStretch(row, 1)

        stack.setCurrentIndex(idx)

    def _on_preview(self):
        """
        Handle parsing the inputs and passing onto the router.
        """

        button = self.findChild(QtGui.QPushButton, 'preview')
        button.setDisabled(True)

        dropdown = self.findChild(QtGui.QComboBox, 'service')
        idx = dropdown.currentIndex()
        vinputs = self.findChild(QtGui.QStackedWidget, 'panels') \
            .widget(idx) \
            .findChildren((QtGui.QComboBox, QtGui.QAbstractSpinBox))
        svc_id = dropdown.itemData(idx)
        options = self._addon.router.get_options(svc_id)

        assert len(options) == len(vinputs)

        text = self.findChild(QtGui.QPlainTextEdit, 'text').toPlainText()
        values = {}

        for i in range(len(options)):
            option, vinput = options[i], vinputs[i]
            values[option['key']] = (
                vinput.value()
                if isinstance(vinput, QtGui.QAbstractSpinBox)
                else vinput.itemData(vinput.currentIndex())
            )

        def callback(exception=None):
            """
            Display any error and re-enable the Preview button.
            """

            if exception:
                import aqt.utils
                aqt.utils.showWarning(exception.message, self)

            button.setDisabled(False)

        self._addon.router.play(svc_id, text, values, callback)

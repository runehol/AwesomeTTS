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
from .common import Label, Note, ICON

# all methods might need 'self' in the future, pylint:disable=R0201


class Dialog(QtGui.QDialog):
    """
    Base used for all dialog windows.
    """

    _FONT_HEADER = QtGui.QFont()
    _FONT_HEADER.setPointSize(12)
    _FONT_HEADER.setBold(True)

    _FONT_INFO = QtGui.QFont()
    _FONT_INFO.setItalic(True)

    _FONT_LABEL = QtGui.QFont()
    _FONT_LABEL.setBold(True)

    _FONT_TITLE = QtGui.QFont()
    _FONT_TITLE.setPointSize(16)
    _FONT_TITLE.setBold(True)

    _SPACING = 10

    __slots__ = [
        '_addon',  # bundle of config, logger, paths, router, version
        '_title',  # description of this window
    ]

    def __init__(self, title, addon, parent):
        """
        Set the modal status for the dialog, sets its layout to the
        return value of the _ui() method, and sets a default title.
        """

        self._addon = addon
        self._addon.logger.debug(
            "Constructing %s (%s) dialog",
            title, self.__class__.__name__,
        )
        self._title = title

        super(Dialog, self).__init__(parent)

        self.setModal(True)
        self.setLayout(self._ui())
        self.setWindowFlags(
            self.windowFlags() &
            ~QtCore.Qt.WindowContextHelpButtonHint
        )
        self.setWindowIcon(ICON)
        self.setWindowTitle(
            title if "AwesomeTTS" in title
            else "AwesomeTTS: " + title
        )

    # UI Construction ########################################################

    def _ui(self):
        """
        Returns a vertical layout with a banner.

        Subclasses should call this method first when overriding so that
        all dialogs have the same banner.
        """

        layout = QtGui.QVBoxLayout()
        layout.addLayout(self._ui_banner())
        layout.addWidget(self._ui_divider(QtGui.QFrame.HLine))

        return layout

    def _ui_banner(self):
        """
        Returns a horizontal layout with some title text, a strecher,
        and version text.

        For subclasses, this method will be called automatically as part
        of the base class _ui() method.
        """

        title = Label(self._title)
        title.setFont(self._FONT_TITLE)

        version = Label("AwesomeTTS\nv" + self._addon.version)
        version.setFont(self._FONT_INFO)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(title)
        layout.addSpacing(self._SPACING)
        layout.addStretch()
        layout.addWidget(version)

        return layout

    def _ui_divider(self, orientation_style=QtGui.QFrame.VLine):
        """
        Returns a divider.

        For subclasses, this method will be called automatically as part
        of the base class _ui() method.
        """

        frame = QtGui.QFrame()
        frame.setFrameStyle(orientation_style | QtGui.QFrame.Sunken)

        return frame

    def _ui_buttons(self):
        """
        Returns a horizontal row of standard dialog buttons, with "OK"
        and "Cancel". If the subclass implements help_request() or
        help_menu(), a "Help" button will also be shown.

        Subclasses must call this method explicitly, at a location of
        their choice. Once called, accept(), reject(), and optionally
        help_request() become wired to the appropriate signals.
        """

        buttons = QtGui.QDialogButtonBox()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        has_help_menu = callable(getattr(self, 'help_menu', None))
        has_help_request = callable(getattr(self, 'help_request', None))

        if has_help_menu or has_help_request:
            if has_help_request:
                buttons.helpRequested.connect(self.help_request)

            buttons.setStandardButtons(
                QtGui.QDialogButtonBox.Help |
                QtGui.QDialogButtonBox.Cancel |
                QtGui.QDialogButtonBox.Ok
            )

        else:
            buttons.setStandardButtons(
                QtGui.QDialogButtonBox.Cancel |
                QtGui.QDialogButtonBox.Ok
            )

        for btn in buttons.buttons():
            if buttons.buttonRole(btn) == QtGui.QDialogButtonBox.AcceptRole:
                btn.setObjectName('okay')
            elif buttons.buttonRole(btn) == QtGui.QDialogButtonBox.RejectRole:
                btn.setObjectName('cancel')
            elif (buttons.buttonRole(btn) == QtGui.QDialogButtonBox.HelpRole
                  and has_help_menu):
                btn.setMenu(self.help_menu(btn))

        return buttons

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Writes a log message and pass onto superclass.
        """

        self._addon.logger.debug("Showing '%s' dialog", self.windowTitle())
        super(Dialog, self).show(*args, **kwargs)

    # Auxiliary ##############################################################

    def _launch_link(self, path):
        """
        Opens a URL on the AwesomeTTS website with the given path.
        """

        url = '/'.join([self._addon.web, path])
        self._addon.logger.debug("Launching %s", url)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))


class ServiceDialog(Dialog):
    """
    Base used for all service-related dialog windows (e.g. single file
    generator, mass file generator, template tag builder).
    """

    _OPTIONS_WIDGETS = (QtGui.QComboBox, QtGui.QAbstractSpinBox)

    _INPUT_WIDGETS = _OPTIONS_WIDGETS + (QtGui.QAbstractButton,
                                         QtGui.QLineEdit, QtGui.QTextEdit)

    __slots__ = [
        '_alerts',       # API to display error messages
        '_panel_built',  # dict, svc_id to True if panel has been constructed
        '_panel_set',    # dict, svc_id to True if panel values have been set
        '_svc_id',       # active service ID
    ]

    def __init__(self, alerts, *args, **kwargs):
        """
        Initialize the mechanism for keeping track of which panels are
        loaded.
        """

        self._alerts = alerts
        self._panel_built = {}
        self._panel_set = {}
        self._svc_id = None

        super(ServiceDialog, self).__init__(*args, **kwargs)

    # UI Construction ########################################################

    def _ui(self):
        """
        Return a services panel and a control panel.
        """

        layout = super(ServiceDialog, self)._ui()

        hor = QtGui.QHBoxLayout()
        hor.addLayout(self._ui_services())
        hor.addSpacing(self._SPACING)
        hor.addWidget(self._ui_divider())
        hor.addSpacing(self._SPACING)
        hor.addLayout(self._ui_control())

        layout.addLayout(hor)
        return layout

    def _ui_services(self):
        """
        Return the service panel, which includes a dropdown for the
        service and a stacked widget for each service's options.
        """

        dropdown = QtGui.QComboBox()
        dropdown.setObjectName('service')

        stack = QtGui.QStackedWidget()
        stack.setObjectName('panels')

        for svc_id, text in self._addon.router.get_services():
            dropdown.addItem(text, svc_id)

            panel = QtGui.QGridLayout()
            panel.addWidget(Label("Pass the following to %s:" % text),
                            0, 0, 1, 2)

            widget = QtGui.QWidget()
            widget.setLayout(panel)

            stack.addWidget(widget)

        dropdown.activated.connect(self._on_service_activated)

        hor = QtGui.QHBoxLayout()
        hor.addWidget(Label("Generate using"))
        hor.addWidget(dropdown)
        hor.addStretch()

        header = Label("Configure Service")
        header.setFont(self._FONT_HEADER)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(header)
        layout.addLayout(hor)
        layout.addWidget(stack)

        return layout

    def _ui_control(self):
        """
        Returns the "Test Settings" header, the text input and a preview
        button.

        Subclasses should either extend this or replace it, but if they
        replace this (e.g. to display the text input differently), the
        objects created must have setObjectName() called with 'text'
        and 'preview'.
        """

        text = QtGui.QLineEdit()
        text.keyPressEvent = lambda key_event: (
            self._on_preview()
            if key_event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]
            else QtGui.QLineEdit.keyPressEvent(text, key_event)
        )
        text.setObjectName('text')
        text.setPlaceholderText("type a phrase to test...")

        button = QtGui.QPushButton("&Preview")
        button.setObjectName('preview')
        button.clicked.connect(self._on_preview)

        hor = QtGui.QHBoxLayout()
        hor.addWidget(text)
        hor.addWidget(button)

        header = Label("Preview")
        header.setFont(self._FONT_HEADER)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(header)
        layout.addLayout(hor)
        layout.addStretch()
        layout.addSpacing(self._SPACING)

        return layout

    # Events #################################################################

    def show(self, *args, **kwargs):
        """
        Recall the last used (or default) service and call in to
        activate its panel, then clear the input text box.
        """

        self._panel_set = {}  # these must be reloaded with each window open

        dropdown = self.findChild(QtGui.QComboBox, 'service')
        idx = max(dropdown.findData(self._addon.config['last_service']), 0)
        dropdown.setCurrentIndex(idx)
        self._on_service_activated(idx, True)

        text = self.findChild(QtGui.QWidget, 'text')
        try:
            text.setText("")
        except AttributeError:
            text.setPlainText("")

        super(ServiceDialog, self).show(*args, **kwargs)

    def help_menu(self, owner):
        """
        Returns a menu that can be attached to the Help button.
        """

        menu = QtGui.QMenu(owner)

        help_svc = QtGui.QAction(menu)
        help_svc.triggered \
            .connect(lambda: self._launch_link('services/' + self._svc_id))
        help_svc.setObjectName('help_svc')

        menu.addAction(
            self.HELP_USAGE_DESC,
            lambda: self._launch_link('usage/' + self.HELP_USAGE_SLUG),
        )
        menu.addAction(help_svc)
        menu.addAction(
            "Enabling other TTS services",
            lambda: self._launch_link('services'),
        )
        return menu

    def _on_service_activated(self, idx, initial=False):
        """
        Construct the target widget if it has not already been built,
        recall the last-used values for the options, and then switch the
        stack to it.
        """

        combo = self.findChild(QtGui.QComboBox, 'service')
        svc_id = combo.itemData(idx)
        stack = self.findChild(QtGui.QStackedWidget, 'panels')

        panel_unbuilt = svc_id not in self._panel_built
        panel_unset = svc_id not in self._panel_set

        if panel_unbuilt or panel_unset:
            widget = stack.widget(idx)
            options = self._addon.router.get_options(svc_id)

            if panel_unbuilt:
                self._panel_built[svc_id] = True
                self._on_service_activated_build(svc_id, widget, options)

            if panel_unset:
                self._panel_set[svc_id] = True
                self._on_service_activated_set(svc_id, widget, options)

        stack.setCurrentIndex(idx)

        if panel_unbuilt and not initial:
            self.adjustSize()

        self._svc_id = svc_id
        self.findChild(QtGui.QAction, 'help_svc') \
            .setText("Using the %s service" % combo.currentText())

    def _on_service_activated_build(self, svc_id, widget, options):
        """
        Based on the list of options, build a grid of labels and input
        controls.
        """

        self._addon.logger.debug("Constructing panel for %s", svc_id)

        row = 1
        panel = widget.layout()

        for option in options:
            label = Label(option['label'])
            label.setFont(self._FONT_LABEL)

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

            else:  # list of tuples
                vinput = QtGui.QComboBox()
                for value, text in option['values']:
                    vinput.addItem(text, value)

                if len(option['values']) == 1:
                    vinput.setDisabled(True)

            panel.addWidget(label, row, 0)
            panel.addWidget(vinput, row, 1)

            row += 1

        label = Note(self._addon.router.get_desc(svc_id))
        label.setFont(self._FONT_INFO)

        panel.addWidget(label, row, 0, 1, 2, QtCore.Qt.AlignBottom)
        panel.setRowStretch(row, 1)

    def _on_service_activated_set(self, svc_id, widget, options):
        """
        Based on the list of options and the user's last known options,
        restore the values of all input controls.
        """

        self._addon.logger.debug("Restoring options for %s", svc_id)

        last_options = self._addon.config['last_options'].get(svc_id, {})
        vinputs = widget.findChildren(self._OPTIONS_WIDGETS)

        assert len(vinputs) == len(options)

        for i in range(len(options)):
            opt, vinput = options[i], vinputs[i]

            if isinstance(opt['values'], tuple):
                try:
                    val = last_options[opt['key']]
                    if not opt['values'][0] <= val <= opt['values'][1]:
                        raise ValueError

                except (KeyError, ValueError):
                    try:
                        val = opt['default']
                        if not opt['values'][0] <= val <= opt['values'][1]:
                            raise ValueError

                    except (KeyError, ValueError):
                        val = opt['values'][0]

                vinput.setValue(val)

            else:
                try:
                    idx = vinput.findData(last_options[opt['key']])
                    if idx < 0:
                        raise ValueError

                except (KeyError, ValueError):
                    try:
                        idx = vinput.findData(opt['default'])
                        if idx < 0:
                            raise ValueError

                    except (KeyError, ValueError):
                        idx = 0

                vinput.setCurrentIndex(idx)

    def _on_preview(self):
        """
        Handle parsing the inputs and passing onto the router.
        """

        svc_id, values = self._get_service_values()
        text_input, text_value = self._get_service_text()
        self._disable_inputs()

        self._addon.router(
            svc_id=svc_id,
            text=self._addon.strip.from_user(text_value),
            options=values,
            callbacks=dict(
                done=lambda: self._disable_inputs(False),
                okay=self._addon.player.preview,
                fail=lambda exception: self._alerts(
                    "The service could not playback the phrase.\n\n%s" %
                    exception.message,
                    self,
                ),
                then=text_input.setFocus,
            ),
        )

    # Auxiliary ##############################################################

    def _disable_inputs(self, flag=True):
        """
        Mass disable (or enable if flag is False) all inputs, except the
        cancel button.
        """

        for widget in (
                widget
                for widget in self.findChildren(self._INPUT_WIDGETS)
                if widget.objectName() != 'cancel'
                and (not isinstance(widget, QtGui.QComboBox) or
                     len(widget) > 1)
        ):
            widget.setDisabled(flag)

    def _get_service_values(self):
        """
        Return the service ID and a dict of all the options.
        """

        dropdown = self.findChild(QtGui.QComboBox, 'service')
        idx = dropdown.currentIndex()
        vinputs = self.findChild(QtGui.QStackedWidget, 'panels') \
            .widget(idx).findChildren(self._OPTIONS_WIDGETS)
        svc_id = dropdown.itemData(idx)
        options = self._addon.router.get_options(svc_id)

        assert len(options) == len(vinputs)

        return svc_id, {
            options[i]['key']:
                vinputs[i].value()
                if isinstance(vinputs[i], QtGui.QAbstractSpinBox)
                else vinputs[i].itemData(vinputs[i].currentIndex())
            for i in range(len(options))
        }

    def _get_service_text(self):
        """
        Return the text box and its phrase.
        """

        text_input = self.findChild(QtGui.QWidget, 'text')
        try:
            text_value = text_input.text()
        except AttributeError:
            text_value = text_input.toPlainText()

        return text_input, text_value

    def _get_all(self):
        """
        Returns a dict of the options that need to be updated to
        remember and process the state of the form.
        """

        svc_id, values = self._get_service_values()
        return {
            'last_service': svc_id,
            'last_options': dict(
                self._addon.config['last_options'].items() +
                [(svc_id, values)]
            ),
        }

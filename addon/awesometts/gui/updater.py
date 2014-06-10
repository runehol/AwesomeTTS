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
Updater dialog
"""

__all__ = ['Updater']

from time import time
from PyQt4 import QtCore, QtGui

from .base import Dialog


class Updater(Dialog):
    """
    Produces a dialog suitable for displaying to the user when an update
    is available, whether the user did a manual update check or if it
    was triggered at start-up.
    """

    _ICON = QtGui.QIcon(':/icons/go-next.png')

    __slots__ = [
        '_version',  # latest version string for the add-on
        '_info',     # dict containing additional information about the update
    ]

    def __init__(self, version, info, *args, **kwargs):  # TODO is_auto/manual
        """
        Builds the dialog with the given version and info.
        """

        self._version = version
        self._info = info

        super(Updater, self).__init__(
            title="Update to v%s" % version,
            *args, **kwargs
        )

    # UI Construction ########################################################

    def _ui(self):
        """
        Returns the superclass's banner follow by our update information
        and action buttons.
        """

        layout = super(Updater, self)._ui()

        if self._info['intro']:
            label = QtGui.QLabel(self._info['intro'])
            label.setTextFormat(QtCore.Qt.PlainText)
            label.setWordWrap(True)
            layout.addWidget(label)

        if self._info['notes']:
            list_widget = QtGui.QListWidget()
            for note in self._info['notes']:
                list_widget.addItem(QtGui.QListWidgetItem(self._ICON, note))
            list_widget.setWordWrap(True)
            layout.addWidget(list_widget)

        if self._info['synopsis']:
            label = QtGui.QLabel(self._info['synopsis'])
            label.setTextFormat(QtCore.Qt.PlainText)
            label.setWordWrap(True)
            layout.addWidget(label)

        layout.addWidget(self._ui_buttons())

        return layout

    def _ui_buttons(self):
        """
        Returns a horizontal row of action buttons. Overrides the one
        from the superclass.
        """

        buttons = QtGui.QDialogButtonBox()

        # TODO if certain risky situations are present (e.g. symlinks or
        # missing Anki interfaces), the now_button should be disabled with an
        # explanation following

        now_button = QtGui.QPushButton("Update the Add-On Now")  # TODO icon?
        now_button.setAutoDefault(False)
        now_button.setDefault(False)
        now_button.clicked.connect(self._update)

        # TODO in manual mode, the later_{menu,button} should be replaced with
        # a simpler "no" button

        later_menu = QtGui.QMenu()
        later_menu.addAction("Remind Me Next Session", self._remind_session)
        later_menu.addAction("Remind Me Tomorrow", self._remind_tomorrow)
        later_menu.addAction("Remind Me in a Week", self._remind_week)
        later_menu.addAction("Skip v%s" % self._version, self._skip_version)
        later_menu.addAction("Stop Checking for Updates", self._disable)

        later_button = QtGui.QPushButton("Not Now")
        later_button.setAutoDefault(False)
        later_button.setDefault(False)
        later_button.setMenu(later_menu)

        buttons.addButton(now_button, QtGui.QDialogButtonBox.YesRole)
        buttons.addButton(later_button, QtGui.QDialogButtonBox.NoRole)

        return buttons

    # Events #################################################################

    def _update(self):
        """
        Updates the add-on via the Anki interface.
        """

        self.accept()

        try:
            pass # TODO via subclassing GetAddons, maybe?
        except Exception, exception:
            pass # TODO

    def _remind_session(self):
        """
        Closes the dialog; add-on will automatically check next session.
        """

        self.reject()

    def _remind_tomorrow(self):
        """
        Bumps the postpone time by 24 hours before closing dialog.
        """

        self._addon.config['updates_postpone'] = time() + 86400
        self.reject()

    def _remind_week(self):
        """
        Bumps the postpone time by 7 days before closing dialog.
        """

        self._addon.config['updates_postpone'] = time() + 604800
        self.reject()

    def _skip_version(self):
        """
        Marks current version as ignored before closing dialog.
        """

        self._addon.config['updates_ignore'] = self._version
        self.reject()

    def _disable(self):
        """
        Disables the automatic updates flag before closing dialog.
        """

        self._addon.config['updates_enabled'] = False
        self.reject()

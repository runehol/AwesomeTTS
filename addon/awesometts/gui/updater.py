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

        # available from parent, but should be overridden
        # layout.addWidget(self._ui_buttons())

        return layout

    # Events #################################################################

    def accept(self):
        """
        TODO
        """

        # TODO

        super(Updater, self).accept()

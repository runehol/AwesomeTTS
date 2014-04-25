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

from PyQt4 import QtGui
from .common import ICON


class Dialog(QtGui.QDialog):
    """
    Base used for all dialog windows.
    """

    __slots__ = [
        '_addon',  # bundle of config, logger, paths, router, version
    ]

    def __init__(self, addon, parent):
        """
        Set the modal status for the dialog and sets its layout to the
        return value of the _ui() method.
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

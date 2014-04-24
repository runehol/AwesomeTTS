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


class Dialog(QtGui.QDialog):
    """
    Base used for all dialog windows.
    """

    __slots__ = [
        '_addon',  # bundle of config, logger, paths, router, version
        '_setup',  # True if the UI has been built out, False otherwise
    ]

    def __init__(self, addon, parent):
        """
        Subclasses must call this method when extending.
        """

        super(Dialog, self).__init__(parent)

        self._addon = addon
        self._setup = False

    def show(self, *args, **kwargs):
        """
        Checks to see if the UI has been built out, runs the restore
        hook, then lets the Qt framework display the window.

        Subclasses should not need to override or extend this method.
        """

        if not self._setup:
            self._build_ui()

        self._restore()

        super(Dialog, self).show(*args, **kwargs)

    # UI Construction ########################################################

    def _build_ui(self):
        """
        Initializes the window as a modal, sets its layout, and marks
        the object as "_setup".

        Subclasses must call this method when overriding.
        """

        self._setup = True

        self.setModal(True)
        self.setLayout(self._create())

    def _create(self):
        """
        Returns a vertical layout with a banner.

        Subclasses should call this method first when overriding.
        """

        layout = QtGui.QVBoxLayout()
        layout.addLayout(self._create_banner())

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

        version = QtGui.QLabel(self._addon.version)
        version_font = QtGui.QFont()
        version_font.setItalic(True)
        version.setFont(version_font)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(version)

        return layout

    def _restore(self):
        """
        Hook that can be optionally overridden by subclasses. Called
        whenever the window is displayed (first time and all successive
        times).
        """


class ServiceDialog(Dialog):
    """
    Base used for all service-related dialog windows (e.g. single file
    generator, mass file generator, template tag builder).
    """

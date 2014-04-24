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
Common reusable GUI elements

Provides a menu action class.
"""

__all__ = ['Action']

from PyQt4 import QtGui


class Action(QtGui.QAction):
    """
    Provides a menu action to trigger a dialog. As everything done from
    the add-on code has to do with AwesomeTTS, these actions all carry a
    speaker icon (if supported by the desktop environment).
    """

    __slots__ = []

    ICON = QtGui.QIcon(':/icons/speaker.png')

    def __init__(self, text, dialog, menu, parent):
        """
        Initializes the menu action, wires its 'triggered' event, and
        adds it to the target menu via Anki's API.
        """

        super(Action, self).__init__(self.ICON, text, parent)

        self.triggered.connect(
            # passed event must be discarded, pylint:disable=W0108
            lambda: dialog.show()
        )

        menu.addAction(self)

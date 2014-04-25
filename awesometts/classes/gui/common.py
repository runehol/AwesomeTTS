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

Provides menu action and button classes.

As everything done from the add-on code has to do with AwesomeTTS, these
all carry a speaker icon (if supported by the desktop environment).
"""

__all__ = ['Action', 'Button']

from PyQt4 import QtCore, QtGui


ICON = QtGui.QIcon(':/icons/speaker.png')


class _Connector(object):  # used like a mixin, pylint:disable=R0903
    """
    Handles deferring construction of the target class until it's
    needed and then keeping a reference to it as long as its triggering
    GUI element still exists.
    """

    def __init__(self, signal, target):
        """
        Store the target for future use and wire up the passed signal.
        """

        self._target = target
        self._instance = None

        signal.connect(self._show)

    def _show(self):
        """
        If the target has not yet been constructed, do so now, and then
        show it.
        """

        if not self._instance:
            self._instance = self._target.constructor(
                *self._target.args,
                **self._target.kwargs
            )

        self._instance.show()


class Action(QtGui.QAction, _Connector):
    """
    Provides a menu action to show a dialog when triggered.
    """

    def __init__(self, target, text, parent):
        """
        Initializes the menu action and wires its 'triggered' event.

        If the specified parent is a QMenu, this new action will
        automatically be added to it.
        """

        QtGui.QAction.__init__(self, ICON, text, parent)
        _Connector.__init__(self, self.triggered, target)

        self.setShortcut('Ctrl+t')

        if isinstance(parent, QtGui.QMenu):
            parent.addAction(self)


class Button(QtGui.QPushButton, _Connector):
    """
    Provides a button to show a dialog when clicked.
    """

    def __init__(self, target, text=None, style=None):
        """
        Initializes the button and wires its 'clicked' event.

        Note that buttons that have text get one set of styling
        different from ones without text.
        """

        QtGui.QPushButton.__init__(self, ICON, text)
        _Connector.__init__(self, self.clicked, target)

        if text:
            self.setIconSize(QtCore.QSize(15, 15))

        else:
            # FIXME How do I localize the tooltip for Mac OS X? (i.e. Cmd+T)
            self.setFixedWidth(20)
            self.setFixedHeight(20)
            self.setFocusPolicy(QtCore.Qt.NoFocus)
            self.setShortcut('Ctrl+t')
            self.setToolTip("Insert an audio clip with AwesomeTTS (Ctrl+T)")

        if style:
            self.setStyle(style)

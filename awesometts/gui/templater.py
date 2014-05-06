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
Template generation dialog
"""

__all__ = ['Templater']

from PyQt4 import QtGui

from .base import ServiceDialog


class Templater(ServiceDialog):
    """
    Provides a dialog for building an on-the-fly TTS tag in Anki's card
    layout editor.
    """

    __slots__ = [
    ]

    def __init__(self, *args, **kwargs):
        """
        Sets our title.
        """

        super(Templater, self).__init__(
            title="Add On-the-Fly TTS Tag",
            *args, **kwargs
        )

    # UI Construction ########################################################

    def _ui_control(self):
        """
        Returns the superclass's text and preview buttons, adding our
        field input selector, then the base class's cancel/OK buttons.
        """

        header = QtGui.QLabel("Source Fields")
        header.setFont(self._FONT_HEADER)

        intro = QtGui.QLabel(
            "During review mode, AwesomeTTS will automatically read the text "
            "from the source field that you specify here, send it to the "
            "service on the left, pass your chosen options, and playback the "
            "result."
        )
        intro.setFont(self._FONT_INFO)
        intro.setWordWrap(True)

        layout = super(Templater, self)._ui_control()
        layout.addWidget(header)
        layout.addWidget(intro)
        layout.addWidget(self._ui_control_field())
        layout.addWidget(self._ui_control_display())
        layout.addWidget(self._ui_buttons())

        return layout

    def _ui_control_field(self):
        """
        Returns a dropdown box to let the user select a source field.
        """

        dropdown = QtGui.QComboBox()
        dropdown.setObjectName('source')
        dropdown.addItem("(insert an empty tag)")
        # TODO populate with fields

        return dropdown

    def _ui_control_display(self):
        """
        Returns a checkbox to let the user set the style on the tag.
        """

        checkbox = QtGui.QCheckBox("Use Inline CSS to Hide the Tag's Content")
        checkbox.setObjectName('hide')

        return checkbox

    def _ui_buttons(self):
        """
        Adjust title of the OK button.
        """

        buttons = super(Templater, self)._ui_buttons()
        buttons.findChild(QtGui.QAbstractButton, 'okay').setText("&Insert")

        return buttons

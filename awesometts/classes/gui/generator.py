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
File generation dialogs
"""

__all__ = ['EditorGenerator']

from .base import ServiceDialog


class EditorGenerator(ServiceDialog):
    """
    Provides a dialog for adding single media files from the editors.
    """

    __slots__ = [
    ]

    def __init__(self, *args, **kwargs):
        """
        Sets our title.
        """

        super(EditorGenerator, self).__init__(*args, **kwargs)
        self.setWindowTitle("Insert TTS File w/ %s" % self.windowTitle())

    # UI Construction ########################################################

    def _ui_control(self):
        """
        Returns the superclass's text and preview buttons, adding the
        base class's cancel/OK buttons.
        """

        layout = super(EditorGenerator, self)._ui_control()
        layout.addWidget(self._ui_buttons())

        return layout

    # Events #################################################################

    def accept(self, *args, **kwargs):
        """
        TODO
        """

        super(EditorGenerator, self).accept(*args, **kwargs)

#!/bin/bash

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2013-2014  Anki AwesomeTTS Development Team
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

if [[ "$1" != *".zip" ]]
then
    echo "Please specify where you want to save the package." 1>&2
    echo 1>&2
    echo "    Usage: $0 <target>" 1>&2
    echo "     e.g.: $0 ~/AwesomeTTS.zip" 1>&2
    exit 1
fi

target=$1
if [[ "$target" != "/"* ]]
then
	target=$PWD/$target
fi

if [[ -e "$target" ]]
then
    echo "$target already exists." 1>&2
    exit 1
fi

oldPwd=$PWD

cd "`dirname "$0"`/.."
./tools/build_ui.sh

cd ..
echo "Packing zip file.."
zip -9R "$target" awesometts/LICENSE.txt \*.py \*.vbs

cd "$oldPwd"

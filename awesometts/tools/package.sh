#!/bin/bash

if [[ "$1" != *".zip" ]]
then
    echo "Please specify where you want to save the package." 1>&2
    echo 1>&2
    echo "    Usage: $0 <target>" 1>&2
    echo "     e.g.: $0 ~/AwesomeTTS.zip" 1>&2
    exit
fi

target=$1
if [[ "$target" != "/"* ]]
then
	target=$PWD/$target
fi

if [[ -e "$target" ]]
then
    echo "$target already exists." 1>&2
    exit
fi

oldPwd=$PWD

cd "`dirname "$0"`/.."
./tools/build_ui.sh

cd ..
echo "Packing zip file.."
zip -9R "$target" awesometts/LICENSE.txt \*.py \*.vbs

cd "$oldPwd"

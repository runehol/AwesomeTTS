#!/bin/bash

if [[ -z "$1" ]]
then
    echo "Please specify your Anki addons directory." 1>&2
    echo 1>&2
    echo "    Usage: $0 <target>" 1>&2
    echo "     e.g.: $0 ~/Anki/addons" 1>&2
    exit
fi

target=$1
if [[ "$target" != "/"* ]]
then
	target=$PWD/$target
fi

if [[ ! -d "$target" ]]
then
    echo "$target is not a directory." 1>&2
    exit
fi

oldPwd=$PWD

cd "`dirname "$0"`/.."
./tools/build_ui.sh

cd ..

echo "Cleaning up.."
rm -fv "$target/AwesomeTTS.py"
rm -fv "$target/AwesomeTTS.pyc"
rm -rfv "$target/awesometts"

echo "Linking.."
ln -sv "$PWD/AwesomeTTS.py" "$target"
ln -sv "$PWD/awesometts" "$target"

cd "$oldPwd"

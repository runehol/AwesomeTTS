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

if [[ -f "$target/awesometts/conf.db" ]]
then
    echo "Saving configuration.."
    saveConf=`mktemp`
    cp -v "$target/awesometts/conf.db" "$saveConf"
fi

oldPwd=$PWD

cd "`dirname "$0"`/.."
./tools/build_ui.sh

cd ..

echo "Cleaning up.."
rm -fv "$target/AwesomeTTS.py"
rm -fv "$target/AwesomeTTS.pyc"
rm -rfv "$target/awesometts"

echo "Installing.."
cp -v AwesomeTTS.py "$target/AwesomeTTS.py"
mkdir -v "$target/awesometts"
cp -v awesometts/*.py "$target/awesometts"
mkdir -v "$target/awesometts/services"
cp -v awesometts/services/*.py awesometts/services/*.vbs "$target/awesometts/services"
mkdir -v "$target/awesometts/forms"
cp -v awesometts/forms/*.py "$target/awesometts/forms"

if [[ -n "$saveConf" ]]
then
    echo "Restoring configuration.."
    mv -v "$saveConf" "$target/awesometts/conf.db"
fi

cd "$oldPwd"

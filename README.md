# AwesomeTTS

AwesomeTTS brings text-to-speech support to Anki, including Ekho, eSpeak,
GoogleTTS, the Mac OS X `say` command, and Microsoft's Speech API (SAPI 5).

More information about the add-on and how to use it can be found on its
[AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613).

## Building and Installing

There are a few different ways one can build/install this add-on.

- **Stable Package:**
  The [AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613) has the
  latest *stable* version of the add-on.

- **Straight Install:**
  Build and copy the files into your Anki `addons` directory using the
  `install.sh` helper, removing any other installation of AwesomeTTS. If you
  have an existing configuration file, it will be saved, but your cache will
  be cleared.

        $ git clone https://github.com/AwesomeTTS/AwesomeTTS.git
        $ ./AwesomeTTS/awesometts/tools/install.sh ~/Anki/addons

- **Using Symlinks for Development:**
  Build and symlink the files into your Anki `addons` directory using the
  `symlink.sh` helper, removing any other installation of AwesomeTTS. If you
  have an existing configuration file, it will be saved, but your cache will
  be cleared _unless_ your new symlink happens to have a cache directory. If
  changes are later made to the `designer/*.ui` files, then just the
  `build_ui.sh` helper by itself can be used to rebuild those.

        $ git clone https://github.com/AwesomeTTS/AwesomeTTS.git
        $ ./AwesomeTTS/awesometts/tools/symlink.sh ~/Anki/addons
            . . .
        $ cd AwesomeTTS/awesometts
        $ ./tools/build_ui.sh

- **Package into a Zip File:**
  Build and package the files into a zip archive for installation somewhere
  else using the `package.sh` helper.

        $ git clone https://github.com/AwesomeTTS/AwesomeTTS.git
        $ AwesomeTTS/awesometts/tools/package.sh ~/AwesomeTTS.zip

# AwesomeTTS

AwesomeTTS brings text-to-speech support to Anki, including Ekho, eSpeak,
GoogleTTS, the Mac OS X `say` command, and Microsoft's Speech API (SAPI 5).

More information about the add-on and how to use it can be found on its
[AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613).

AwesomeTTS is free and open source software, released under version 3 of the
GNU General Public License.

## Building and Installing

There are a few different ways one can build/install this add-on.

### Stable Package

The [AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613) has the
latest [stable branch](https://github.com/AwesomeTTS/AwesomeTTS/tree/stable)
of the add-on, which can be installed directly within the Anki user interface
using add-on code `301952613`.

### Development and Other Versions

The [develop branch](https://github.com/AwesomeTTS/AwesomeTTS/tree/develop),
[hotfixes and previews](https://github.com/AwesomeTTS/AwesomeTTS/branches),
and [specific releases](https://github.com/AwesomeTTS/AwesomeTTS/releases) can
be pulled in and installed with Git.

- **Straight Install:**
  Build and copy the files into your Anki `addons` directory using the
  `install.sh` helper, removing any other installation of AwesomeTTS. If you
  have an existing configuration file, it will be saved, but your cache will
  be cleared.

        $ git clone https://github.com/AwesomeTTS/AwesomeTTS.git
        $ cd AwesomeTTS
        $ git checkout [ref]  (if not using "develop", e.g. pre/v1.0-beta11)
        $ awesometts/tools/install.sh [addons directory]  (e.g. ~/Anki/addons)

- **Using Symlinks for Development:**
  Build and symlink the files into your Anki `addons` directory using the
  `symlink.sh` helper, removing any other installation of AwesomeTTS. If you
  have an existing configuration file, it will be saved, but your cache will
  be cleared _unless_ your new symlink happens to have a cache directory.

        $ git clone https://github.com/AwesomeTTS/AwesomeTTS.git
        $ cd AwesomeTTS
        $ git checkout [ref]  (if not using "develop", e.g. pre/v1.0-beta11)
        $ awesometts/tools/symlink.sh [addons directory]  (e.g. ~/Anki/addons)

- **Package into a Zip File:**
  Build and package the files into a zip archive for installation somewhere
  else using the `package.sh` helper. This is also how the package is built
  for AnkiWeb.

        $ git clone https://github.com/AwesomeTTS/AwesomeTTS.git
        $ cd AwesomeTTS
        $ git checkout [ref]  (if not using "develop", e.g. pre/v1.0-beta11)
        $ awesometts/tools/package.sh [zip target]  (e.g. ~/AwesomeTTS.zip)

# AwesomeTTS, with some additions

This is a fork of the [AwesomeTTS add-on](https://github.com/imsys/AwesomeTTS)
maintained by [Arthur Helfstein Fragoso](https://github.com/imsys) for the
[Anki flashcard program](http://ankisrs.net/).

More information about the original add-on can be found on its
[AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613).

## Building and Installing

There are a few different ways one can build/install this fork.

- **Straight Install:**
  Build and copy the files into your Anki `addons` directory using the
  `install.sh` helper, removing any other installation of AwesomeTTS. If you
  have an existing configuration file, it will be saved, but your cache will be
  cleared.

        $ git clone https://github.com/corpulentcoffee/AwesomeTTS.git
        $ ./AwesomeTTS/awesometts/tools/install.sh ~/Anki/addons

- **Using Symlinks for Development:**
  Build and symlink the files into your Anki `addons` directory using the
  `symlink.sh` helper, removing any other installation of AwesomeTTS. If you
  have an existing configuration file, it will be saved, but your cache will be
  cleared _unless_ your new symlink happens to have a cache directory. If
  changes are later made to the `designer/*.ui` files, then just the
  `build_ui.sh` helper by itself can be used to rebuild those.

        $ git clone https://github.com/corpulentcoffee/AwesomeTTS.git
        $ ./AwesomeTTS/awesometts/tools/symlink.sh ~/Anki/addons
            . . .
        $ cd AwesomeTTS/awesometts
        $ ./tools/build_ui.sh

- **Package into a Zip File:**
  Build and package the files into a zip archive for installation somewhere else
  using the `package.sh` helper.

        $ git clone https://github.com/corpulentcoffee/AwesomeTTS.git
        $ AwesomeTTS/awesometts/tools/package.sh ~/AwesomeTTS.zip

## Added Features

### Caching/Offline Support for On-the-Fly Google TTS

Ordinarily, the download URL for every unique on-the-fly `<tts>` tag is passed
to `mplayer` for it to stream, and the file must be downloaded again each time
the tag is encountered (e.g. for reviews of the same card).

This fork adds caching support for these downloads such that when the "cache
downloads from Google TTS" checkbox is enabled on the Configuration screen, the
MP3s are instead downloaded to disk and the path of the downloaded MP3 is passed
to `mplayer`.

Caching the files locally has the benefit of speeding up successive reviews of
cards and also allows the TTS functionality to continue working when network
connectivity isn't available (assuming, of course, that the given `<tts>` tag
has been encountered at least once before).

The files in cache directory are handled by hashing the phrases within each
`<tts>` tag after some minimal normalization (e.g. removal of excess whitespace
and HTML). The cache directory can be emptied from the user interface with the
"Clear Cache" button on the Configuration screen.

### Updated Language List

Google has added some additional languages to their TTS service since AwesomeTTS
1.0 Beta 10 was released.

This fork adds support for Bosnian (`bs`), Esperanto (`eo`), Tamil (`ta`), and
Thai (`th`) to be processed.

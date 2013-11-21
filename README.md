# AwesomeTTS, with some additions

This is a fork of the [AwesomeTTS add-on](https://github.com/imsys/AwesomeTTS)
maintained by [Arthur Helfstein Fragoso](https://github.com/imsys) for the
[Anki flashcard program](http://ankisrs.net/).

More information about the original add-on can be found on its
[AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613).

Assuming Anki is already installed but the original AwesomeTTS add-on is not,
one way to activate this alternate version is to clone the repository, build
the user interface, and then symlink it into Anki's `addons` directory, e.g.

    $ git clone https://github.com/corpulentcoffee/AwesomeTTS.git
    $ cd AwesomeTTS/awesometts
    $ tools/build_ui.sh
    $ cd ..
    $ ln -s $PWD/awesometts ~/Anki/addons
    $ ln -s $PWD/AwesomeTTS.py ~/Anki/addons

## Caching/Offline Support for On-the-Fly Google TTS

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

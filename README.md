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

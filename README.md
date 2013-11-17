# AwesomeTTS, with some additions

This is a fork of the [AwesomeTTS add-on](https://github.com/imsys/AwesomeTTS)
maintained by [Arthur Helfstein Fragoso](https://github.com/imsys) for the
[Anki flashcard program](http://ankisrs.net/).

More information about the original add-on can be found on its
[AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613).

Assuming Anki is already installed but the original AwesomeTTS add-on is not,
one way to activate this alternate version is to just clone the repository and
symlink it into Anki's `addons` directory, e.g.

    $ git clone https://github.com/corpulentcoffee/AwesomeTTS.git
    $ ln -s $PWD/AwesomeTTS/awesometts ~/Anki/addons
    $ ln -s $PWD/AwesomeTTS/AwesomeTTS.py ~/Anki/addons

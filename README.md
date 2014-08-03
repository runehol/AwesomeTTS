# AwesomeTTS

AwesomeTTS brings text-to-speech functionality to [Anki](http://ankisrs.net),
with support for several local and web-based TTS services.

More information and documentation for using the add-on can be found on its
[website](https://ankiatts.appspot.com). User reviews of the add-on can be
found on its [AnkiWeb add-on page](https://ankiweb.net/shared/info/301952613).

This repository holds two interconnected projects:

- [AwesomeTTS add-on code](addon/), which runs within Anki
- [website and update API web service](web/), which runs on Google App Engine
  and helps users get the most out of the add-on


## Licenses

AwesomeTTS is free and open source software. The add-on code that runs within
Anki is released under the [GNU GPL v3](addon/LICENSE.txt), and first-party
web code is released under the [GNU AGPL v3](web/LICENSE.txt).

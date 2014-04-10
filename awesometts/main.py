# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2013-2014  Dave Shifflett
# Copyright (C) 2012       Dusan Arsenijevic
# Copyright (C) 2013       mistaecko on GitHub
# Copyright (C) 2013       PtrToVoid on GitHub
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


version = '1.0 Beta 11 (develop)'

import os, re, types, time
from PyQt4.QtCore import SIGNAL, Qt, QObject
from PyQt4.QtGui import (
    QAction,
    QComboBox,
    QDialog,
    QIcon,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from anki import sound
from anki.hooks import addHook, wrap
from aqt import mw, utils
from aqt.reviewer import Reviewer

from awesometts import conf
import awesometts.forms as forms
import awesometts.services as services
from .paths import CACHE_DIR, relative


TTS_service = {  # TODO consider moving into services package's __init__
    service_key: service_def

    for service_module in [
        getattr(services, package_name)
        for package_name
        in dir(services)
        if not package_name.startswith('_') and not package_name.endswith('_')
    ]
    if hasattr(service_module, 'TTS_service')

    for (service_key, service_def) in service_module.TTS_service.items()
}


######## utils
def playTTSFromText(text):
    tospeakHTML = getTTSFromHTML(text)
    tospeak = getTTSFromText(text)
    for service, html_tags in tospeakHTML.items():
        for html_tag in html_tags:
            TTS_service[service]['play'](
                ''.join(html_tag.findAll(text=True)),
                html_tag['voice'],
            )
    for service, bracket_tags in tospeak.items():
        for bracket_tag in bracket_tags:
            match = re.match(r'(.*?):(.*)', bracket_tag, re.M|re.I)
            TTS_service[service]['play'](match.group(2), match.group(1))

def getTTSFromText(text):
    tospeak = {}
    for match in re.findall(r"\[(G)TTS:(.*?)\]|\[A?TTS:(.*?):(.*?)\]", text, re.M|re.I):
        service = match[0].lower() if match[0] else match[2].lower()
        value = match[1] if match[0] else match[3]
        if not tospeak.has_key(service):
            tospeak.update({service: [value]})
        else:
            tospeak[service].append(value)
    return tospeak

def getTTSFromHTML(html):
    from BeautifulSoup import BeautifulSoup

    soup = BeautifulSoup(html)
    tospeakhtml = {}

    for htmltag in soup('tts'):
        service = htmltag['service'].lower()
        text = ''.join(htmltag.findAll(text=True)) #get all the text from the tag and stips html
        if text == None or text == '' or text.isspace():
            continue #skip empty tags
        if not tospeakhtml.has_key(service):
            tospeakhtml.update({service: [htmltag]})
        else:
            tospeakhtml[service].append(htmltag)
    return tospeakhtml


############################ Service Forms

def service_form(module, parent):
    lookup = sorted([
        (service_key, service_def, QComboBox())
        for service_key, service_def
        in TTS_service.items()
    ], key=lambda service: service[1]['name'].lower())

    dialog = QDialog(parent)

    form = module.Ui_Dialog()
    form.setupUi(dialog)

    form.comboBoxService.addItems([service[1]['name'] for service in lookup])
    form.comboBoxService.currentIndexChanged.connect(
        form.stackedWidget.setCurrentIndex
    )

    for service_key, service_def, combo_box in lookup:
        combo_box.addItems([voice[1] for voice in service_def['voices']])
        # TODO recall last-used voice, then combo_box.setCurrentIndex(xxx)

        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(QLabel("Voice:"))
        vertical_layout.addWidget(combo_box)

        stack_widget = QWidget(form.stackedWidget)
        stack_widget.setLayout(vertical_layout)
        form.stackedWidget.addWidget(stack_widget)

        if service_key == conf.last_service:
            form.comboBoxService.setCurrentIndex(
                form.stackedWidget.count() - 1
            )

    return lookup, dialog, form

def service_form_values(form, lookup):
    selected = form.comboBoxService.currentIndex()
    service_key, service_def, combo_box = lookup[selected]
    voice = service_def['voices'][combo_box.currentIndex()][0]

    return service_key, service_def, voice


############################ MP3 File Generator

# TODO: It would be nice if a service that sometimes cannot fulfill given
# text (e.g. one using a finite set of prerecorded dictionary words) be made
# to explicitly return False or an exception (instead of None) from its play
# and record callables so that there would be some sort of notification to the
# user that the entered text is not playable.
#
# A convention for this can be established as soon as AwesomeTTS begins
# shipping with at least one bundled service that sometimes returns without
# successfully playing back some text.

def ATTS_Factedit_button(editor):
    lookup, dialog, form = service_form(forms.filegenerator, editor.widget)

    def execute(preview):
        text = form.texttoTTS.toPlainText().strip()
        if not text:
            return

        service_key, service_def, voice = service_form_values(form, lookup)

        if preview:
            service_def['play'](unicode(text), voice)
        else:
            conf.last_service = service_key
            # TODO set last-used voice

            filename = service_def['record'](text, voice)  # FIXME unicode()?
            if filename:
                editor.addMedia(filename)
            else:
                utils.showWarning("No audio available for text.")

    form.previewbutton.clicked.connect(lambda: execute(preview=True))
    if dialog.exec_():
        execute(preview=False)


def ATTS_Fact_edit_setupFields(self):
    AwesomeTTS = QPushButton(self.widget)
    AwesomeTTS.setFixedHeight(20)
    AwesomeTTS.setFixedWidth(20)
    AwesomeTTS.setCheckable(True)
    AwesomeTTS.connect(AwesomeTTS, SIGNAL("clicked()"), lambda self=self: ATTS_Factedit_button(self))
    AwesomeTTS.setIcon(QIcon(":/icons/speaker.png"))
    AwesomeTTS.setToolTip("AwesomeTTS :: MP3 File Generator")
    AwesomeTTS.setShortcut("Ctrl+g")
    AwesomeTTS.setFocusPolicy(Qt.NoFocus)
    self.iconsBox.addWidget(AwesomeTTS)
    AwesomeTTS.setStyle(self.plastiqueStyle)


addHook("setupEditorButtons", ATTS_Fact_edit_setupFields)


############################ MP3 Mass Generator

srcField = -1
dstField = -1



#take a break, so we don't fall in Google's blacklist. Code contributed by Dusan Arsenijevic
def take_a_break(ndone, ntotal):
    t = 500
    while True:
        mw.progress.update(label="Generated %s of %s, \n sleeping for %s seconds...." % (ndone+1, ntotal, t))
        time.sleep(1)
        t = t-1
        if t == 0:
            break

def generate_audio_files(notes, form, service_def, voice, source_field, dest_field):
    update_count = 0
    skip_counts = {
        key: [0, message]
        for key, message
        in [
            ('fields', 'Missing source and/or destination field'),
            ('empty', 'Empty value in the source field'),
            ('unfulfilled', 'Service returned an empty response'),
        ]
    }

    nelements = len(notes)
    batch = 900
    throttle = 'throttle' in service_def and service_def['throttle']

    if not form.radioOverwrite.isChecked() and form.checkBoxSndTag.isChecked():
        RE_SOUND = re.compile(r'\[sound:[^\]]+\]', re.IGNORECASE)

    for c, id in enumerate(notes):
        if throttle and (c+1)%batch == 0: # GoogleTTS has to take a break once in a while
            take_a_break(c, nelements)
        note = mw.col.getNote(id)

        if not (source_field in note.keys() and dest_field in note.keys()):
            skip_counts['fields'][0] += 1
            continue

        mw.progress.update(label="Generating MP3 files...\n%s of %s\n%s" % (c+1, nelements, note[source_field]))

        if note[source_field] == '' or note[source_field].isspace(): #check if the field is blank
            skip_counts['empty'][0] += 1
            continue

        filename = service_def['record'](
            note[source_field],  # FIXME unicode()?
            voice,
        )

        if filename:
            if form.radioOverwrite.isChecked():
                if form.checkBoxSndTag.isChecked():
                    note[dest_field] = '[sound:'+ filename +']'
                else:
                    note[dest_field] = filename
            else:
                if form.checkBoxSndTag.isChecked():
                    note[dest_field] = RE_SOUND.sub(
                        '',
                        note[dest_field],
                    ).strip()
                note[dest_field] += ' [sound:'+ filename +']'

            update_count += 1
            note.flush()

        else:
            skip_counts['unfulfilled'][0] += 1

    return nelements, update_count, skip_counts.values()


def onGenerate(browser):
    notes = browser.selectedNotes()
    if not notes:
        utils.showInfo("Select notes before using the MP3 Mass Generator.")
        return

    # TODO it would be nice if this only included fields from selected notes
    import anki.find
    fields = sorted(anki.find.fieldNames(mw.col, downcase=False))

    lookup, dialog, form = service_form(forms.massgenerator, browser)

    form.sourceFieldComboBox.addItems(fields)
    # TODO recall last-used source, then form.sourceFieldComboBox.setCurrentIndex(xxx)

    form.destinationFieldComboBox.addItems(fields)
    # TODO recall last-used dest, then form.destinationFieldComboBox.setCurrentIndex(xxx)

    form.label_version.setText("Version %s" % version)

    def dest_handling_changed():
        """Update checkbox label given the new handling behavior."""
        form.checkBoxSndTag.setText(
            dest_handling_changed.OVERWRITE_TEXT
            if form.radioOverwrite.isChecked()
            else dest_handling_changed.ENDOF_TEXT
        )
    dest_handling_changed.ENDOF_TEXT = form.checkBoxSndTag.text()
    dest_handling_changed.OVERWRITE_TEXT = "Wrap Path in [sound:xxx] Tag"

    form.radioEndof.toggled.connect(dest_handling_changed)
    form.radioOverwrite.toggled.connect(dest_handling_changed)

    if not dialog.exec_():
        return

    service_key, service_def, voice = service_form_values(form, lookup)

    source_field = fields[form.sourceFieldComboBox.currentIndex()]
    dest_field = fields[form.destinationFieldComboBox.currentIndex()]
    # TODO set last-used fields

    conf.last_service = service_key
    # TODO set last-used voice

    browser.mw.checkpoint("AwesomeTTS MP3 Mass Generator")
    browser.mw.progress.start(immediate=True, label="Generating MP3 files...")

    browser.model.beginReset()

    process_count, update_count, skip_counts = generate_audio_files(
        notes,
        form,
        service_def,
        voice,
        source_field,
        dest_field,
    )

    browser.model.endReset()
    browser.mw.progress.finish()

    if process_count == update_count:
        utils.showInfo(
            "Note processed and updated." if process_count == 1
            else "%d notes processed and updated." % process_count
        )

    elif process_count == 1:
        utils.showWarning("\n".join(
            ["Could not process note:"] +
            [message for count, message in skip_counts if count],
        ))

    else:
        utils.showWarning("\n".join([
            "Of the %d processed notes..." % process_count,
            "",
        ] + [
            "- %s: %d %s" % (
                message,
                count,
                "note" if count == 1 else "notes",
            )
            for count, message
            in [(update_count, "Successful update")] + skip_counts
            if count
        ]))


def setupMenu(browser):
    a = QAction("AwesomeTTS MP3 Mass Generator", browser)
    browser.form.menuEdit.addAction(a)
    browser.connect(a, SIGNAL("triggered()"), lambda b=browser: onGenerate(b))

addHook("browser.setupMenus", setupMenu)

######### Configurator

def KeyToString(val):
    if val:
        for k, v in vars(Qt).iteritems():
            if v == val and k[:4] == "Key_":
                return k[4:]
        return 'Unknown'
    else:
        return 'Unassigned'

def Conf_keyPressEvent(dialog_buttons_tuple, e):
    dialog, buttons = dialog_buttons_tuple
    buttons = [button for button in buttons if button.getkey]

    if not buttons:
        if e.key() == Qt.Key_Escape:
            dialog.reject()
        return

    for button in buttons:
        button.keyval = (
            None if e.key() in [
                Qt.Key_Escape,
                Qt.Key_Backspace,
                Qt.Key_Delete
            ]
            else e.key()
        )
        button.setText(KeyToString(button.keyval))
        button.getkey = False

def getKey(button):
    button.setText("Press a new hotkey")
    button.getkey = True

def editConf():
    d = QDialog()

    form = forms.configurator.Ui_Dialog()
    form.setupUi(d)

    form.pushKeyQ.getkey = form.pushKeyA.getkey = False
    d.keyPressEvent = types.MethodType(
        Conf_keyPressEvent,
        (d, [form.pushKeyQ, form.pushKeyA]),
    )
    form.pushKeyQ.keyval = conf.tts_key_q
    form.pushKeyQ.setText(KeyToString(form.pushKeyQ.keyval))
    form.pushKeyA.keyval = conf.tts_key_a
    form.pushKeyA.setText(KeyToString(form.pushKeyA.keyval))

    form.cAutoQ.setChecked(conf.automatic_questions)
    form.cAutoA.setChecked(conf.automatic_answers)
    form.cSubprocessing.setChecked(conf.subprocessing)
    form.cCaching.setChecked(conf.caching)

    form.lame_flags_edit.setText(conf.lame_flags)

    QObject.connect(form.pushKeyQ, SIGNAL("clicked()"), lambda form=form: getKey(form.pushKeyQ))
    QObject.connect(form.pushKeyA, SIGNAL("clicked()"), lambda form=form: getKey(form.pushKeyA))

    cacheListing = (
        [
            filename
            for filename
            in os.listdir(CACHE_DIR)
            if filename.endswith('.mp3')
        ]
        if os.path.isdir(CACHE_DIR)
        else []
    )
    cacheCount = len(cacheListing)

    if cacheCount > 0:
        import locale
        locale.setlocale(locale.LC_ALL, '')

        form.pushClearCache.setEnabled(True)
        form.pushClearCache.setText(
            'Clear Cache (%s item%s)' %
            (
                locale.format('%d', cacheCount, grouping=True),
                cacheCount != 1 and 's' or ''
            )
        )

        def pushClearCacheClicked():
            form.pushClearCache.setEnabled(False)

            countSuccess = 0
            countError = 0
            for cacheFilepath in cacheListing:
                try:
                    os.remove(relative(
                        CACHE_DIR,
                        cacheFilepath,
                    ))
                    countSuccess += 1
                except OSError:
                    countError += 1

            if countError > 0:
                if countSuccess > 0:
                    form.pushClearCache.setText(
                        'Partially Emptied Cache (%s item%s remaining)' %
                        (
                            locale.format('%d', countError, grouping=True),
                            countError != 1 and 's' or ''
                        )
                    )
                else:
                    form.pushClearCache.setText('Unable to Empty Cache')
            else:
                form.pushClearCache.setText('Successfully Emptied Cache')
        form.pushClearCache.clicked.connect(pushClearCacheClicked)

    else:
        form.pushClearCache.setEnabled(False)
        form.pushClearCache.setText('Clear Cache (no items)')

    d.setWindowModality(Qt.WindowModal)

    form.label_version.setText("Version "+ version)

    if not d.exec_():
        return

    conf.update(
        tts_key_q=form.pushKeyQ.keyval,
        tts_key_a=form.pushKeyA.keyval,
        automatic_questions=form.cAutoQ.isChecked(),
        automatic_answers=form.cAutoA.isChecked(),
        subprocessing=form.cSubprocessing.isChecked(),
        caching=form.cCaching.isChecked(),
        lame_flags=form.lame_flags_edit.text(),
    )


# create a new menu item, "test"
menuconf = QAction("AwesomeTTS", mw)
# set it to call testFunction when it's clicked
mw.connect(menuconf, SIGNAL("triggered()"), editConf)
# and add it to the tools menu
mw.form.menuTools.addAction(menuconf)




######################################### Keys and AutoRead

## Check pressed key
def newKeyHandler(self, evt):
    pkey = evt.key()
    if self.state == 'answer' or self.state == 'question':
        if pkey == conf.tts_key_q:
            playTTSFromText(self.card.q())  #read the TTS tags
        if self.state == 'answer' and pkey == conf.tts_key_a:
            playTTSFromText(self.card.a()) #read the TTS tags
    evt.accept()



def ATTSautoread(toread, automatic):
    if not sound.hasSound(toread):
        if automatic:
            playTTSFromText(toread)

def ATTS_OnQuestion(self):
    ATTSautoread(self.card.q(), conf.automatic_questions)

def ATTS_OnAnswer(self):
    ATTSautoread(self.card.a(), conf.automatic_answers)



Reviewer._keyHandler = wrap(Reviewer._keyHandler, newKeyHandler, "before")
Reviewer._showQuestion = wrap(Reviewer._showQuestion, ATTS_OnQuestion, "after")
Reviewer._showAnswer = wrap(Reviewer._showAnswer, ATTS_OnAnswer, "after")

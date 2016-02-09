# -*- coding: utf-8 -*-

import os
import sys
import re
import shutil
import subprocess
from pathlib import Path
from yaml import load
from argparse import ArgumentParser
from bottle import mako_template
from autoupgrade import AutoUpgrade
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QMessageBox

from edocuments.main_widget import MainWindow

CONFIG_FILENAME = "edocuments.yaml"

if 'APPDATA' in os.environ:
    CONFIG_PATH = os.path.join(os.environ['APPDATA'], CONFIG_FILENAME)
elif 'XDG_CONFIG_HOME' in os.environ:
    CONFIG_PATH = os.path.join(os.environ['XDG_CONFIG_HOME'], CONFIG_FILENAME)
else:
    CONFIG_PATH = os.path.join(os.environ['HOME'], '.config', CONFIG_FILENAME)

config = {}
root_folder = None
settings = None


def gui_main():
    global config, root_folder, settings
    with open(CONFIG_PATH) as f:
        config = load(f.read())
    root_folder = "%s/%s/" % (
        os.path.expanduser('~'),
        config.get("root_folder"),
    )
    settings = QSettings("org", "edocuments")

    app = QApplication(sys.argv)
    mw = MainWindow()
    if settings.value("geometry") is not None:
        mw.restoreGeometry(settings.value("geometry"))
    if settings.value("state") is not None:
        mw.restoreState(settings.value("state"))

    au = AutoUpgrade('edocuments')
    if au.check():
        msg = QMessageBox(mw)
        msg.setWindowTitle("eDocuments - Upgrade")
        msg.setText("A new version is available")
        msg.setInformativeText("Do you want to do anupdate and restart?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec()
        if ret == QMessageBox.Yes:
            au.upgrade(dependencies=True)
            au.restart()

    mw.show()
    app.exec()
    settings.setValue("geometry", mw.saveGeometry())
    settings.setValue("state", mw.saveState())
    settings.sync()


def cmd_main():
    parser = ArgumentParser(
        description='eDocuments - a simple and productive personal documents '
        'library.',
        prog=sys.argv[0]
    )
    parser.add_argument(
        '--install', action='store_true',
        help='Install the application icon, the required packages, '
        'and default config file',
    )
    parser.add_argument(
        '--lang3', default='eng', metavar='LANG',
        help='the language used by the OCR',
    )
    parser.add_argument(
        '--list-available-lang3', action='store_true',
        help='List the available language used by the OCR.',
    )
    options = parser.parse_args()

    if options.list_available_lang3:
        if Path('/usr/bin/apt-cache').exists():
            result = subprocess.check_output([
                '/usr/bin/apt-cache', 'search', 'tesseract-ocr-'])
            result = str(result)[1:].strip("'")
            result = result.replace('\\n', '\n')
            result = re.sub(
                '\ntesseract-ocr-all - [^\n]* packages\n',
                '', result, flags=re.MULTILINE)
            result = re.sub(r'tesseract-ocr-', '', result)
            result = re.sub(r' - tesseract-ocr language files ', ' ', result)
            print(result)
        else:
            exit('Works only on Debian base OS')

    if options.install:
        if not Path(os.path.expanduser(
                    '~/.local/share/applications')).exists():
            os.makedirs(os.path.expanduser('~/.local/share/applications'))
        ressource_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), 'ressources')
        shutil.copyfile(
            os.path.join(ressource_dir, 'edocuments.desktop'),
            os.path.expanduser(
                '~/.local/share/applications/edocuments.desktop')
        )
        shutil.copyfile(
            os.path.join(ressource_dir, 'edocuments.png'),
            os.path.expanduser('~/.local/share/applications/edocuments.png')
        )
        config = mako_template(
            os.path.join(ressource_dir, 'config.yaml'),
            lang=options.lang3
        )
        with open(
            os.path.expanduser('~/.config/edocuments.yaml'), 'w'
        ) as file_open:
            file_open.write(config)
        if Path('/usr/bin/apt-get').exists():
            subprocess.check_call([
                'sudo', 'apt-get', 'install',
                'python3-pyqt5', 'sane-utils', 'imagemagick',
                'tesseract-ocr', 'tesseract-ocr-' + options.lang3,
                'optipng'])
        else:
            print(
                'WARNING: the package installation works only on Debian '
                'base OS')

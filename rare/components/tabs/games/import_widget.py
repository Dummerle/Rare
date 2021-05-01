import json
import os
import string
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QLineEdit, \
    QGroupBox
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from rare.utils import legendary_utils
from rare.utils.extra_widgets import PathEdit

logger = getLogger("Import")


class ImportWidget(QWidget):
    update_list = pyqtSignal()

    def __init__(self, core: LegendaryCore, parent):
        super(ImportWidget, self).__init__(parent=parent)
        self.core = core
        self.game_list = [i.app_name for i in self.core.get_game_list()]

        self.main_layout = QHBoxLayout()
        self.back_button = QPushButton(icon("mdi.keyboard-backspace", color="white"), self.tr("Back"))
        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.back_button)
        self.right_layout.addStretch(1)
        self.main_layout.addLayout(self.right_layout)
        self.back_button.setFixedWidth(75)
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>Import Game</h2")
        self.layout.addWidget(self.title)

        # self.import_one_game = QLabel(f"<h3>{self.tr('Import existing game from Epic Games Launcher')}</h3>")
        self.import_one_game = QGroupBox(self.tr('Import existing game from Epic Games Launcher'))
        self.import_one_game.setObjectName("group")
        self.gb_layout = QVBoxLayout()

        self.import_game_info = QLabel(self.tr("Select path to game"))
        self.gb_layout.addWidget(self.import_game_info)

        self.override_app_name_label = QLabel(
            self.tr("Override app name (Only if imported game from legendary or the app could not find the app name)"))
        self.override_app_name_label.setWordWrap(True)
        self.app_name_input = QLineEdit()
        self.app_name_input.setFixedHeight(32)
        minilayout = QHBoxLayout()
        minilayout.addStretch(1)
        self.indicator_label = QLabel("")
        minilayout.addWidget(self.indicator_label)
        self.app_name_input.setLayout(minilayout)
        self.app_name_input.textChanged.connect(self.app_name_changed)

        self.path_edit = PathEdit(os.path.expanduser("~"), QFileDialog.DirectoryOnly, edit_func=self.path_changed)
        self.gb_layout.addWidget(self.path_edit)

        self.gb_layout.addWidget(self.override_app_name_label)
        self.gb_layout.addWidget(self.app_name_input)

        self.info_label = QLabel("")
        self.gb_layout.addWidget(self.info_label)
        self.import_button = QPushButton(self.tr("Import Game"))
        self.gb_layout.addWidget(self.import_button)
        self.import_button.clicked.connect(self.import_game)

        self.import_one_game.setLayout(self.gb_layout)

        self.layout.addWidget(self.import_one_game)

        self.layout.addStretch(1)

        self.auto_import = QLabel(f"<h3>{self.tr('Auto import all existing games')}</h3>")
        self.layout.addWidget(self.auto_import)
        self.auto_import_button = QPushButton(self.tr("Import all games from Epic Games Launcher"))
        self.auto_import_button.clicked.connect(self.import_games_prepare)
        self.layout.addWidget(self.auto_import_button)
        self.layout.addStretch(1)

        self.main_layout.addLayout(self.layout)
        # self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)

    def app_name_changed(self, text):
        if text in self.game_list:
            self.indicator_label.setPixmap(icon("ei.ok-sign", color="green").pixmap(16, 16))
        else:
            self.indicator_label.setPixmap(icon("ei.remove-sign", color="red").pixmap(16, 16))

    def path_changed(self, path):
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, ".egstore")):
                self.app_name_input.setText(self.find_app_name(path))

    def find_app_name(self, path):
        if not os.path.exists(os.path.join(path, ".egstore")):
            return None
        for i in os.listdir(os.path.join(path, ".egstore")):
            if i.endswith(".mancpn"):
                file = os.path.join(path, ".egstore", i)
                break
        else:
            logger.warning("File was not found")
            return None
        return json.load(open(file, "r"))["AppName"]

    def import_game(self, path=None):
        app_name = self.app_name_input.text()
        if not path:
            path = self.path_edit.text()
        if not app_name:
            # try to find app name
            if a_n := self.find_app_name(path):
                app_name = a_n
            else:
                self.info_label.setText(self.tr("Could not find app name"))
                return

        if legendary_utils.import_game(self.core, app_name=app_name, path=path):
            self.info_label.setText(self.tr("Successfully imported {}. Reload library").format(
                self.core.get_installed_game(app_name).title))
            self.app_name_input.setText("")

            self.update_list.emit()
        else:
            logger.warning("Failed to import" + app_name)
            self.info_label.setText(self.tr("Failed to import {}").format(app_name))
            return

    def auto_import_games(self, game_path):
        imported = 0
        if not os.path.exists(game_path):
            return 0
        if os.listdir(game_path) == 0:
            logger.info(f"No Games found in {game_path}")
            return 0
        for path in os.listdir(game_path):
            json_path = game_path + path
            if not os.path.isdir(json_path):
                logger.info(f"Game at {game_path + path} doesn't exist")
                continue
            app_name = self.find_app_name(json_path)
            if not app_name:
                logger.warning("Could not find app name at " + game_path)
                continue

            if legendary_utils.import_game(self.core, app_name, game_path + path):
                imported += 1
        return imported

    def import_games_prepare(self):
        # Automatically import from windows
        imported = 0
        if os.name == "nt":
            available_drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
            for drive in available_drives:
                path = f"{drive}/Program Files/Epic Games/"
                if os.path.exists(path):
                    imported += self.auto_import_games(path)

        else:
            possible_wineprefixes = [os.path.expanduser("~/.wine"), os.path.expanduser("~/Games/epic-games-store")]
            for wine_prefix in possible_wineprefixes:
                imported += self.auto_import_games(os.path.join(wine_prefix, "drive_c/Program Files/Epic Games/"))
        if imported > 0:
            QMessageBox.information(self, "Imported Games",
                                    self.tr("Successfully imported {} Games. Reloading Library").format(imported))
            self.update_list.emit()
        else:
            QMessageBox.information(self, "Imported Games", self.tr("No Games were found"))

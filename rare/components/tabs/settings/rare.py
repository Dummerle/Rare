import os
import shutil
import subprocess
import sys
from logging import getLogger

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog, QComboBox, QPushButton, QCheckBox, QWidget, QSpacerItem, QSizePolicy

from rare.components.tabs.settings.rpc_settings import RPCSettings
from rare.components.tabs.settings.settings_widget import SettingsWidget
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import get_lang, get_possible_langs
from .rare_ui import Ui_RareSettings

logger = getLogger("RareSettings")

languages = [
    ("en", "English"),
    ("de", "Deutsch"),
    ("fr", "Français")
]


class RareSettings(QWidget, Ui_RareSettings):
    def __init__(self):
        super(RareSettings, self).__init__()
        self.setupUi(self)

        # (option_name, group_text, checkbox_text, default
        self.checkboxes = [
            ("sys_tray", self.tr("Hide to System Tray Icon"), self.tr("Exit to System Tray Icon"), True),
            ("auto_update", self.tr("Automatically update Games on startup"), self.tr("Auto updates"),
             False),
            ("confirm_start", self.tr("Confirm launch of game"), self.tr("Confirm launch of game"),
             False),
            ("auto_sync_cloud", self.tr("Auto sync with cloud"), self.tr("Sync with cloud"), True),
            ("notification", self.tr("Show Notifications after Downloads"), self.tr("Show notification"),
             True),
            ("save_size", self.tr("Save size of window after restart"), self.tr("Save size"), False)
        ]

        self.settings = QSettings()
        img_dir = self.settings.value("img_dir", os.path.expanduser("~/.cache/rare/images/"), type=str)
        language = self.settings.value("language", get_lang(), type=str)
        # select Image dir
        self.select_path = PathEdit(img_dir, type_of_file=QFileDialog.DirectoryOnly)
        self.select_path.text_edit.textChanged.connect(lambda t: self.save_path_button.setDisabled(False))
        self.save_path_button = QPushButton(self.tr("Save"))
        self.save_path_button.clicked.connect(self.save_path)
        self.img_dir = SettingsWidget(self.tr("Image Directory"), self.select_path, self.save_path_button)
        self.layout().replaceWidget(self.img_dir_ph, self.img_dir)

        # Select lang
        self.select_lang = QComboBox()
        self.select_lang.addItems([i[1] for i in languages])
        if language in get_possible_langs():
            index = [lang[0] for lang in languages].index(language)
            self.select_lang.setCurrentIndex(index)
        else:
            self.select_lang.setCurrentIndex(0)
        self.lang_widget = SettingsWidget(self.tr("Language"), self.select_lang)
        self.select_lang.currentIndexChanged.connect(self.update_lang)
        self.layout().replaceWidget(self.lang_widget_ph, self.lang_widget)

        self.rpc = RPCSettings()
        self.layout().replaceWidget(self.rpc_ph, self.rpc)

        self.settings_widget = SettingsWidget("Behaviour", None)
        for option, head_text, text, default in self.checkboxes:
            checkbox = SettingsCheckbox(option, text, default)
            checkbox.setToolTip(head_text)
            self.settings_widget.layout.addWidget(checkbox)
        self.settings_widget.layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.layout().replaceWidget(self.settings_widget_ph, self.settings_widget)

        self.open_log_dir = QPushButton(self.tr("Open Log directory"))
        self.open_log_dir.clicked.connect(self.open_dir)
        self.layout().addWidget(self.open_log_dir)

    def open_dir(self):
        logdir = os.path.expanduser("~/.cache/rare/logs")
        if os.name == "nt":
            os.startfile(logdir)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.Popen([opener, logdir])

    def save_window_size(self):
        self.settings.setValue("save_size", self.save_size.isChecked())
        self.settings.remove("window_size")

    def save_path(self):
        self.save_path_button.setDisabled(True)
        self.update_path()

    def update_lang(self, i: int):
        self.settings.setValue("language", languages[i][0])
        self.lang_widget.info_text.setText(self.tr("Restart Application to activate changes"))

    def update_path(self):
        old_path = self.settings.value("img_dir", type=str)
        new_path = self.select_path.text()

        if old_path != new_path:
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            elif len(os.listdir(new_path)) > 0:
                logger.warning("New directory is not empty")
                return
            logger.info("Move Images")
            for i in os.listdir(old_path):
                shutil.move(os.path.join(old_path, i), os.path.join(new_path, i))
            os.rmdir(old_path)
            self.settings.setValue("img_dir", new_path)


class SettingsCheckbox(QCheckBox):
    def __init__(self, option, text, default):
        super(SettingsCheckbox, self).__init__(text)
        self.option = option
        self.settings = QSettings()
        self.setChecked(self.settings.value(option, default, bool))
        self.stateChanged.connect(lambda: self.settings.setValue(option, self.isChecked()))

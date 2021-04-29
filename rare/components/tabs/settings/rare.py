import os
import shutil
import subprocess
import sys
from logging import getLogger

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog, QWidget

from rare.components.tabs.settings.rare_ui import Ui_RareSettings
from rare.components.tabs.settings.rpc_settings import RPCSettings
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import get_lang, get_possible_langs

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

        # (widget_name, option_name, default)
        self.checkboxes = [
            (self.sys_tray, "sys_tray", True),
            (self.auto_update, "auto_update", False),
            (self.confirm_start, "confirm_start", False),
            (self.auto_sync_cloud, "auto_sync_cloud", True),
            (self.notification, "notification", True),
            (self.save_size, "save_size", False)
       ]

        self.settings = QSettings()
        self.img_dir_path = self.settings.value("img_dir", os.path.expanduser("~/.cache/rare/images/"), type=str)
        language = self.settings.value("language", get_lang(), type=str)

        # Select Image directory
        self.img_dir = PathEdit(self.img_dir_path, file_type=QFileDialog.DirectoryOnly)
        self.img_dir.text_edit.textChanged.connect(lambda t: self.img_dir.save_path_button.setDisabled(False))
        self.img_dir.save_path_button.clicked.connect(self.save_path)
        self.img_dir.save_path_button.setDisabled(True)
        self.layout_img_dir.addWidget(self.img_dir)

        # Select lang
        self.select_lang.addItems([i[1] for i in languages])
        if language in get_possible_langs():
            index = [lang[0] for lang in languages].index(language)
            self.select_lang.setCurrentIndex(index)
        else:
            self.select_lang.setCurrentIndex(0)
        self.info_lang.setVisible(False)
        self.select_lang.currentIndexChanged.connect(self.update_lang)

        self.rpc = RPCSettings()
        self.layout_rpc.addWidget(self.rpc)

        self.init_checkboxes(self.checkboxes)
        self.sys_tray.stateChanged.connect(
            lambda: self.settings.setValue("sys_tray", self.sys_tray.isChecked())
        )
        self.auto_update.stateChanged.connect(
            lambda: self.settings.setValue("auto_update", self.auto_update.isChecked())
        )
        self.confirm_start.stateChanged.connect(
            lambda: self.settings.setValue("confirm_start", self.confirm_start.isChecked())
        )
        self.auto_sync_cloud.stateChanged.connect(
            lambda: self.settings.setValue("auto_sync_cloud", self.auto_sync_cloud.isChecked())
        )
        self.notification.stateChanged.connect(
            lambda: self.settings.setValue("notification", self.notification.isChecked())
        )
        self.save_size.stateChanged.connect(
            lambda: self.settings.setValue("save_size", self.save_size.isChecked())
        )

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
        self.img_dir.save_path_button.setDisabled(True)
        self.update_path()

    def update_lang(self, i: int):
        self.settings.setValue("language", languages[i][0])
        self.info_lang.setVisible(True)

    def update_path(self):
        old_path = self.img_dir_path
        new_path = self.img_dir.text()

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
            self.img_dir_path = new_path
            self.settings.setValue("img_dir", new_path)

    def init_checkboxes(self, checkboxes):
        for cb in checkboxes:
            widget, option, default = cb
            widget.setChecked(self.settings.value(option, default, bool))

import os

from PyQt5.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QSpinBox, QFileDialog, QLabel, QPushButton, QHBoxLayout, \
    QCheckBox

from custom_legendary.core import LegendaryCore
from rare.utils.extra_widgets import PathEdit


class InstallDialog(QDialog):
    infos = 0

    def __init__(self, app_name, core: LegendaryCore, update=False):
        super(InstallDialog, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core
        self.game = self.core.get_game(app_name)
        self.form = QFormLayout()
        self.update_game = update
        self.layout.addWidget(QLabel(self.tr("<h3>Install {}</h3>").format(self.game.app_title)))

        if self.core.lgd.config.has_option("Legendary", "install_dir"):
            default_path = self.core.lgd.config.get("Legendary", "install_dir")
        else:
            default_path = os.path.expanduser("~/legendary")
        if not default_path:
            default_path = os.path.expanduser("~/legendary")
        if not update:
            self.install_path_field = PathEdit(text=default_path, file_type=QFileDialog.DirectoryOnly)
            self.form.addRow(QLabel("Install directory"), self.install_path_field)

        if self.core.lgd.config.has_option("Legendary", "max_workers"):
            max_workers = self.core.lgd.config.get("Legendary", "max_workers")
        else:
            max_workers = 0

        self.max_workes = QSpinBox()
        self.max_workes.setValue(int(max_workers))
        self.form.addRow(QLabel(self.tr("Max workers (0: Default)")), self.max_workes)

        self.force = QCheckBox()
        self.force.setChecked(False)
        self.form.addRow(QLabel(self.tr("Force download")), self.force)

        self.ignore_free_space = QCheckBox()
        self.ignore_free_space.setChecked(False)
        self.form.addRow(QLabel(self.tr("Ignore free space (Warning!)")), self.ignore_free_space)

        self.layout.addLayout(self.form)

        self.ok_btn = QPushButton("Next")
        self.ok_btn.clicked.connect(self.ok)
        self.cancel = QPushButton("Cancel")
        self.cancel.clicked.connect(lambda: self.close())

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok_btn)
        self.button_layout.addWidget(self.cancel)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def get_information(self, path=None):
        if path:
            self.install_path_field.text_edit.setText(path)
        self.exec_()
        return self.infos

    def ok(self):
        self.infos = self.install_path_field.text() if not self.update_game else None, self.max_workes.value(), self.force.isChecked(), self.ignore_free_space.isChecked()
        self.close()


class InstallInfoDialog(QDialog):
    accept: bool = False

    def __init__(self, dl_size, install_size):
        super(InstallInfoDialog, self).__init__()
        self.layout = QVBoxLayout()
        self.infos = QLabel(self.tr(
            "Download size: {}GB\nInstall size: {}GB").format(round(dl_size / 1024 ** 3, 2),
                                                              round(install_size / 1024 ** 3, 2)))
        self.layout.addWidget(self.infos)

        self.btn_layout = QHBoxLayout()
        self.install_btn = QPushButton(self.tr("Install"))
        self.install_btn.clicked.connect(self.install)
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.cancel)
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.install_btn)
        self.btn_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.btn_layout)

        self.setLayout(self.layout)

    def get_accept(self):
        self.exec_()
        return self.accept

    def install(self):
        self.accept = True
        self.close()

    def cancel(self):
        self.accept = False
        self.close()

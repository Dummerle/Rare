import os

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox, QFileDialog, QPushButton, QMessageBox, QLineEdit, \
    QScrollArea, QCheckBox

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame, Game
from rare.components.tabs.settings.linux import LinuxSettings
from rare.components.tabs.settings.settings_widget import SettingsWidget
from rare.utils.extra_widgets import PathEdit


def find_proton_wrappers():
    possible_proton_wrappers = []
    try:
        compatibilitytools_dirs = [
            os.path.expanduser("~/.steam/steam/steamapps/common"),
            "/usr/share/steam/compatibilitytools.d"
        ]
        for c in compatibilitytools_dirs:
            for i in os.listdir(c):
                proton = os.path.join(c, i, "proton")
                vdf = os.path.join(c, i, "compatibilitytool.vdf")
                if os.path.exists(proton) and os.path.exists(vdf):
                    wrapper = '"' + proton + '" run'
                    possible_proton_wrappers.append(wrapper)
    except FileNotFoundError as e:
        print("Unable to find any Proton version")
    return possible_proton_wrappers


class GameSettings(QScrollArea):
    game: Game
    igame: InstalledGame

    # variable to no update when changing game
    change = False

    def __init__(self, core: LegendaryCore, parent):
        super(GameSettings, self).__init__(parent=parent)
        self.core = core
        self.widget = QWidget()
        self.settings = QSettings()
        self.setWidgetResizable(True)
        self.layout = QVBoxLayout()
        self.title = QLabel("Error")
        self.layout.addWidget(self.title)

        self.offline = QComboBox()
        self.offline.addItems(["unset", "true", "false"])
        self.offline_widget = SettingsWidget(self.tr("Launch Game offline"), self.offline)
        self.offline.currentIndexChanged.connect(lambda x: self.update_combobox(x, "offline"))

        self.skip_update = QComboBox()
        self.skip_update.addItems(["unset", "true", "false"])
        self.skip_update_widget = SettingsWidget(self.tr("Skip update check before launching"), self.skip_update)
        self.layout.addWidget(self.skip_update_widget)
        self.skip_update.currentIndexChanged.connect(lambda x: self.update_combobox(x, "skip_update_check"))

        self.launch_params = QLineEdit("")
        self.launch_params.setPlaceholderText(self.tr("Start parameter"))
        self.launch_params_accept_button = QPushButton(self.tr("Save"))
        self.launch_params_widget = SettingsWidget(self.tr("Launch parameters"), self.launch_params,
                                                   self.launch_params_accept_button)
        self.layout.addWidget(self.launch_params_widget)
        self.launch_params_accept_button.clicked.connect(
            lambda: self.save_line_edit("start_params", self.launch_params.text()))

        self.cloud_sync = QCheckBox("Sync with cloud")
        self.cloud_sync_widget = SettingsWidget(self.tr("Auto sync with cloud"), self.cloud_sync)
        self.layout.addWidget(self.cloud_sync_widget)
        self.cloud_sync.stateChanged.connect(lambda: self.settings.setValue(f"{self.game.app_name}/auto_sync_cloud",
                                                                            self.cloud_sync.isChecked()))

        self.layout.addWidget(self.offline_widget)

        self.wrapper = QLineEdit("")
        self.wrapper.setPlaceholderText("Wrapper")
        self.wrapper_save_button = QPushButton(self.tr("Save"))
        self.wrapper_save_button.clicked.connect(lambda: self.save_line_edit("wrapper", self.wrapper.text()))
        self.wrapper_widget = SettingsWidget(self.tr("Wrapper (e.g. optirun)"), self.wrapper, self.wrapper_save_button)
        self.layout.addWidget(self.wrapper_widget)

        if os.name != "nt":
            self.possible_proton_wrappers = find_proton_wrappers()

            self.select_proton = QComboBox()
            self.select_proton.addItems(["Don't use Proton"] + self.possible_proton_wrappers)
            self.select_proton.currentIndexChanged.connect(self.change_proton)
            self.select_proton_widget = SettingsWidget(self.tr("Proton Wrapper"), self.select_proton)
            self.layout.addWidget(self.select_proton_widget)

            self.proton_prefix = PathEdit("x", QFileDialog.DirectoryOnly)
            self.proton_prefix.save_path_button.clicked.connect(self.update_prefix)
            self.proton_prefix_widget = SettingsWidget(self.tr("Proton prefix"), self.proton_prefix)
            self.layout.addWidget(self.proton_prefix_widget)

            self.linux_settings = LinuxAppSettings(core)
            self.layout.addWidget(self.linux_settings)

        # startparams, skip_update_check

        self.layout.addStretch(1)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def save_line_edit(self, option, value):
        if value != "":
            if not (self.game.app_name in self.core.lgd.config.sections()):
                self.core.lgd.config.add_section(self.game.app_name)
            self.core.lgd.config.set(self.game.app_name, option, value)
        else:
            if self.game.app_name in self.core.lgd.config.sections() and self.core.lgd.config.get(
                    f"{self.game.app_name}", option, fallback="") != "":
                self.core.lgd.config.remove_option(self.game.app_name, option)
            if not self.core.lgd.config.get(self.game.app_name):
                self.core.lgd.config.remove_section(self.game.app_name)
        self.core.lgd.save_config()

    def update_combobox(self, i, option):
        if self.change:
            # remove section
            if i == 0:
                if self.game.app_name in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}", option, fallback="") != "":
                        self.core.lgd.config.remove_option(self.game.app_name, option)
                if self.core.lgd.config[self.game.app_name] == {}:
                    self.core.lgd.config.remove_section(self.game.app_name)
            elif i == 1:
                self.core.lgd.config.add_section(self.game.app_name)
                self.core.lgd.config.set(self.game.app_name, option, "true")
            elif i == 2:
                self.core.lgd.config.add_section(self.game.app_name)
                self.core.lgd.config.set(self.game.app_name, option, "false")
            self.core.lgd.save_config()

    def change_proton(self, i):
        if self.change:
            # Dont use Proton
            if i == 0:
                self.proton_prefix_widget.setVisible(False)
                self.wrapper_widget.setVisible(True)
                if f"{self.game.app_name}" in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}", "wrapper", fallback="") != "":
                        self.core.lgd.config.remove_option(self.game.app_name, "wrapper")
                    if self.core.lgd.config.get(f"{self.game.app_name}", "no_wine", fallback="") != "":
                        self.core.lgd.config.remove_option(self.game.app_name, "no_wine")
                    if self.core.lgd.config[self.game.app_name] == {}:
                        self.core.lgd.config.remove_section(self.game.app_name)
                if f"{self.game.app_name}.env" in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}.env", "STEAM_COMPAT_DATA_PATH",
                                                fallback="") != "":
                        self.core.lgd.config.remove_option(f"{self.game.app_name}.env", "STEAM_COMPAT_DATA_PATH")
                    if self.core.lgd.config[self.game.app_name + ".env"] == {}:
                        self.core.lgd.config.remove_section(self.game.app_name + ".env")
            else:
                self.proton_prefix_widget.setVisible(True)
                self.wrapper_widget.setVisible(False)
                wrapper = self.possible_proton_wrappers[i - 1]
                if not self.game.app_name in self.core.lgd.config.sections():
                    self.core.lgd.config[self.game.app_name] = {}
                if not self.game.app_name + ".env" in self.core.lgd.config.sections():
                    self.core.lgd.config[self.game.app_name + ".env"] = {}
                self.core.lgd.config.set(self.game.app_name, "wrapper", wrapper)
                self.core.lgd.config.set(self.game.app_name, "no_wine", "true")
                self.core.lgd.config.set(self.game.app_name + ".env", "STEAM_COMPAT_DATA_PATH",
                                         os.path.expanduser("~/.proton"))
                self.proton_prefix.text_edit.setText(os.path.expanduser("~/.proton"))

                # Dont use Wine
                self.linux_settings.wine_exec.text_edit.setText("")
                self.linux_settings.save_setting(self.linux_settings.wine_exec, "wine_exec")
                self.linux_settings.wine_prefix.text_edit.setText("")
                self.linux_settings.save_setting(self.linux_settings.wine_prefix, "wine_prefix")

        self.core.lgd.save_config()

    def update_prefix(self):
        text = self.proton_prefix.text()
        if text == "":
            text = os.path.expanduser("~/.proton")
            self.proton_prefix.text_edit.setText(text)
        if not os.path.exists(text):
            try:
                os.makedirs(text)
            except PermissionError:
                QMessageBox.warning(self, "Warning", self.tr("No permission to create folder"))
                text = os.path.expanduser("~/.proton")
                self.proton_prefix.text_edit.setText(text)

        self.core.lgd.config.set(self.game.app_name + ".env", "STEAM_COMPAT_DATA_PATH", text)
        self.core.lgd.save_config()

    def update_game(self, app_name):
        self.change = False
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(app_name)

        if self.igame.can_run_offline:
            offline = self.core.lgd.config.get(self.game.app_name, "offline", fallback="unset")
            if offline == "true":
                self.offline.setCurrentIndex(1)
            elif offline == "false":
                self.offline.setCurrentIndex(2)
            else:
                self.offline.setCurrentIndex(0)

            self.offline_widget.setVisible(True)
        else:
            self.offline_widget.setVisible(False)

        skip_update = self.core.lgd.config.get(self.game.app_name, "skip_update_check", fallback="unset")
        if skip_update == "true":
            self.skip_update.setCurrentIndex(1)
        elif skip_update == "false":
            self.skip_update.setCurrentIndex(2)
        else:
            self.skip_update.setCurrentIndex(0)

        wrapper = self.core.lgd.config.get(self.game.app_name, "wrapper", fallback="")
        self.wrapper.setText(wrapper)

        self.title.setText(f"<h2>{self.game.app_title}</h2>")
        if os.name != "nt":
            self.linux_settings.update_game(app_name)
            self.linux_settings.dxvk.update_settings(app_name)
            proton = self.core.lgd.config.get(f"{app_name}", "wrapper", fallback="").replace('"', "")
            if proton != "":
                self.proton_prefix_widget.setVisible(True)
                self.select_proton.setCurrentText(f'"{proton.replace(" run", "")}" run')
                proton_prefix = self.core.lgd.config.get(f"{app_name}.env", "STEAM_COMPAT_DATA_PATH",
                                                         fallback=self.tr(
                                                             "Please select path for proton prefix"))
                self.proton_prefix.text_edit.setText(proton_prefix)
                self.wrapper_widget.setVisible(False)
            else:
                self.select_proton.setCurrentIndex(0)
                self.proton_prefix_widget.setVisible(False)
                self.wrapper_widget.setVisible(True)

        if not self.game.supports_cloud_saves:
            self.cloud_sync_widget.setVisible(False)
        else:
            self.cloud_sync_widget.setVisible(True)
            sync_cloud = self.settings.value(f"{self.game.app_name}/auto_sync_cloud", True, bool)
            self.cloud_sync.setChecked(sync_cloud)

        self.launch_params.setText(self.core.lgd.config.get(self.game.app_name, "start_params", fallback=""))
        self.change = True


class LinuxAppSettings(LinuxSettings):
    def __init__(self, core):
        super(LinuxAppSettings, self).__init__(core, "app")

    def update_game(self, app_name):
        self.name = app_name
        self.wine_prefix.text_edit.setText(self.core.lgd.config.get(self.name, "wine_prefix", fallback=""))
        self.wine_exec.text_edit.setText(self.core.lgd.config.get(self.name, "wine_executable", fallback=""))
        self.dxvk.name = app_name
        self.dxvk.more_settings_widget.name = app_name

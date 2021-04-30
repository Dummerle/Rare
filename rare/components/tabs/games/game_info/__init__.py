import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QKeyEvent
from PyQt5.QtWidgets import QWidget, QTabWidget, QMessageBox
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame, Game
from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.components.tabs.games.game_info.dlcs import DlcTab
from rare.components.tabs.games.game_info.game_settings import GameSettings
from rare.ui.components.tabs.games.game_info.game_info import Ui_GameInfo
from rare.utils import legendary_utils
from rare.utils.extra_widgets import SideTabBar
from rare.utils.legendary_utils import VerifyThread
from rare.utils.utils import IMAGE_DIR, get_size


class InfoTabs(QTabWidget):
    def __init__(self, core, parent):
        super(InfoTabs, self).__init__(parent=parent)
        self.app_name = ""
        self.core = core
        self.setTabBar(SideTabBar())
        self.setTabPosition(QTabWidget.West)

        self.addTab(QWidget(), icon("mdi.keyboard-backspace", color="white"), self.tr("Back"))
        self.tabBarClicked.connect(lambda x: self.parent().layout.setCurrentIndex(0) if x == 0 else None)

        self.info = GameInfo(core, self)
        self.addTab(self.info, self.tr("Game Info"))

        self.settings = GameSettings(core, self)
        self.addTab(self.settings, self.tr("Settings"))
        self.tabBar().setCurrentIndex(1)

        self.dlc_tab = DlcTab(core, self)
        self.addTab(self.dlc_tab, self.tr("DLCs"))

    def update_game(self, app_name, dlcs: list):

        self.info.update_game(app_name)
        self.settings.update_game(app_name)

        # DLC Tab: Disable if no dlcs available
        if len(dlcs[self.core.get_game(app_name).asset_info.catalog_item_id]) == 0:
            self.setTabEnabled(3, False)
        else:
            self.setTabEnabled(3, True)
            self.dlc_tab.update_dlcs(app_name, dlcs)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().layout.setCurrentIndex(0)


class GameInfo(QWidget, Ui_GameInfo):
    igame: InstalledGame
    game: Game
    update_list = pyqtSignal()
    verify_game = pyqtSignal(str)
    verify_threads = {}

    def __init__(self, core: LegendaryCore, parent):
        super(GameInfo, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = core

        self.uninstall_button.clicked.connect(self.uninstall)
        self.verify_button.clicked.connect(self.verify)
        self.repair_button.clicked.connect(self.repair)

    def uninstall(self):
        infos = UninstallDialog(self.game).get_information()
        if infos == 0:
            print("Cancel Uninstall")
            return
        legendary_utils.uninstall(self.game.app_name, self.core, infos)
        self.update_list.emit()

    def repair(self):
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f'{self.game.app_name}.repair')
        if not os.path.exists(repair_file):
            QMessageBox.warning(self, "Warning", self.tr(
                "Repair file does not exist or game does not need a repair. Please verify game first"))
            return
        self.verify_game.emit(self.game.app_name)

    def verify(self):
        self.verify_widget.setCurrentIndex(1)
        verify_thread = VerifyThread(self.core, self.game.app_name)
        verify_thread.status.connect(self.verify_satistics)
        verify_thread.summary.connect(self.finish_verify)
        verify_thread.start()
        self.verify_progress.setValue(0)
        self.verify_threads[self.game.app_name] = verify_thread

    def verify_satistics(self, progress):
        # checked, max, app_name
        if progress[2] == self.game.app_name:
            self.verify_progress.setValue(progress[0] * 100 / progress[1])

    def finish_verify(self, failed):
        failed, missing, app_name = failed
        if failed == 0 and missing == 0:
            QMessageBox.information(self, "Summary",
                                    "Game was verified successfully. No missing or corrupt files found")
        else:
            ans = QMessageBox.question(self, "Summary", self.tr(
                'Verification failed, {} file(s) corrupted, {} file(s) are missing. Do you want to repair them?').format(
                failed, missing), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ans == QMessageBox.Yes:
                self.verify_game.emit(self.game.app_name)
        self.verify_widget.setCurrentIndex(0)
        self.verify_threads.pop(app_name)

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(app_name)

        self.game_title.setText(f"<h2>{self.game.app_title}</h2>")

        if os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/FinalArt.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/FinalArt.png")
        elif os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxTall.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxTall.png")
        elif os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxLogo.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxLogo.png")
        else:
            # logger.warning(f"No Image found: {self.game.title}")
            pixmap = None
        if pixmap:
            w = 200
            pixmap = pixmap.scaled(w, int(w * 4 / 3))
            self.image.setPixmap(pixmap)
        self.app_name.setText(self.game.app_name)
        self.version.setText(self.game.app_version)
        self.dev.setText(self.game.metadata["developer"])
        self.install_size.setText(get_size(self.igame.install_size))
        self.install_path.setText(self.igame.install_path)

        if len(self.verify_threads.keys()) == 0 or not self.verify_threads.get(app_name):
            self.verify_widget.setCurrentIndex(0)
        elif self.verify_threads.get(app_name):
            self.verify_widget.setCurrentIndex(1)
            self.verify_progress.setValue(
                self.verify_threads[app_name].num / self.verify_threads[app_name].total * 100)

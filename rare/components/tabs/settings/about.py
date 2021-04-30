import webbrowser

from PyQt5.QtWidgets import QWidget

from rare import __version__
from rare.ui.components.tabs.settings.about import Ui_About
from rare.utils.utils import get_latest_version


def versiontuple(v):
    try:
        return tuple(map(int, (v.split("."))))
    except:
        return tuple((9, 9, 9))  # It is a beta version and newer


class About(QWidget, Ui_About):
    def __init__(self):
        super(About, self).__init__()
        self.setupUi(self)

        self.version.setText(__version__)

        self.update_label.setVisible(False)
        self.update.setVisible(False)
        self.open_browser.setVisible(False)

        latest_tag = get_latest_version()
        self.update_available = versiontuple(latest_tag) > versiontuple(__version__)

        self.update.setText("{} -> {}".format(__version__, latest_tag))

        self.open_browser.clicked.connect(
            lambda: webbrowser.open("https://github.com/Dummerle/Rare/releases/latest"))

        if self.update_available:
            print(f"Update available: {__version__} -> {latest_tag}")
            self.update_label.setVisible(True)
            self.update.setVisible(True)
            self.open_browser.setVisible(True)

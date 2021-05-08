import json
import os
import shutil
import sys
from logging import getLogger

import requests
from PIL import Image, UnidentifiedImageError
from PyQt5.QtCore import pyqtSignal, QLocale, QSettings

from rare import lang_path, __version__, style_path
from custom_legendary.core import LegendaryCore

logger = getLogger("Utils")
s = QSettings("Rare", "Rare")
IMAGE_DIR = s.value("img_dir", os.path.expanduser("~/.cache/rare/images"), type=str)
logger.info("IMAGE DIRECTORY: " + IMAGE_DIR)


def download_images(signal: pyqtSignal, core: LegendaryCore):
    if not os.path.isdir(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        logger.info("Create Image dir")

    # Download Images
    games, dlcs = core.get_game_and_dlc_list()
    dlc_list = []
    for i in dlcs.values():
        dlc_list.append(i[0])
    game_list = games + dlc_list
    for i, game in enumerate(game_list):
        try:
            download_image(game)
        except json.decoder.JSONDecodeError:
            shutil.rmtree(f"{IMAGE_DIR}/{game.app_name}")
            download_image(game)
        signal.emit(i/len(game_list)*100)


def download_image(game, force=False):
    if force and os.path.exists(f"{IMAGE_DIR}/{game.app_name}"):
        shutil.rmtree(f"{IMAGE_DIR}/{game.app_name}")
    if not os.path.isdir(f"{IMAGE_DIR}/" + game.app_name):
        os.mkdir(f"{IMAGE_DIR}/" + game.app_name)

    # to git picture updates
    if not os.path.isfile(f"{IMAGE_DIR}/{game.app_name}/image.json"):
        json_data = {"DieselGameBoxTall": None, "DieselGameBoxLogo": None, "Thumbnail": None}
    else:
        json_data = json.load(open(f"{IMAGE_DIR}/{game.app_name}/image.json", "r"))
    # Download
    for image in game.metadata["keyImages"]:
        if image["type"] == "DieselGameBoxTall" or image["type"] == "DieselGameBoxLogo" or image["type"] == "Thumbnail":
            if image["type"] not in json_data.keys():
                json_data[image["type"]] = None
            if json_data[image["type"]] != image["md5"] or not os.path.isfile(
                    f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png"):
                # Download
                json_data[image["type"]] = image["md5"]
                # os.remove(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png")
                json.dump(json_data, open(f"{IMAGE_DIR}/{game.app_name}/image.json", "w"))
                logger.info(f"Download Image for Game: {game.app_title}")
                url = image["url"]
                with open(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png", "wb") as f:
                    f.write(requests.get(url).content)
                    try:
                        img = Image.open(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png")
                        img = img.resize((200, int(200*4/3)))
                        img.save(f"{IMAGE_DIR}/{game.app_name}/{image['type']}.png")
                    except UnidentifiedImageError as e:
                        logger.warning(e)

    # scale and grey
    if not os.path.isfile(f'{IMAGE_DIR}/' + game.app_name + '/UninstalledArt.png'):

        if os.path.isfile(f'{IMAGE_DIR}/' + game.app_name + '/DieselGameBoxTall.png'):
            # finalArt = Image.open(f'{IMAGE_DIR}/' + game.app_name + '/DieselGameBoxTall.png')
            # finalArt.save(f'{IMAGE_DIR}/{game.app_name}/FinalArt.png')
            # And same with the grayscale one

            bg = Image.open(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png")
            uninstalledArt = bg.convert('L')
            uninstalledArt = uninstalledArt.resize((200, int(200*4/3)))
            uninstalledArt.save(f'{IMAGE_DIR}/{game.app_name}/UninstalledArt.png')
        elif os.path.isfile(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png"):
            bg: Image.Image = Image.open(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png")
            bg = bg.resize((int(bg.size[1] * 3 / 4), bg.size[1]))
            logo = Image.open(f'{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png').convert('RGBA')
            wpercent = ((bg.size[0] * (3 / 4)) / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((int(bg.size[0] * (3 / 4)), hsize), Image.ANTIALIAS)
            # Calculate where the image has to be placed
            pasteX = int((bg.size[0] - logo.size[0]) / 2)
            pasteY = int((bg.size[1] - logo.size[1]) / 2)
            # And finally copy the background and paste in the image
            # finalArt = bg.copy()
            # finalArt.paste(logo, (pasteX, pasteY), logo)
            # Write out the file
            # finalArt.save(f'{IMAGE_DIR}/' + game.app_name + '/FinalArt.png')
            logoCopy = logo.copy()
            logoCopy.putalpha(int(256 * 3 / 4))
            logo.paste(logoCopy, logo)
            uninstalledArt = bg.copy()
            uninstalledArt.paste(logo, (pasteX, pasteY), logo)
            uninstalledArt = uninstalledArt.convert('L')
            uninstalledArt.save(f'{IMAGE_DIR}/' + game.app_name + '/UninstalledArt.png')
        else:
            logger.warning(f"File {IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png doesn't exist")


def get_lang():
    core = LegendaryCore()
    if "Legendary" in core.lgd.config.sections() and "locale" in core.lgd.config["Legendary"]:
        logger.info("Found locale in Legendary config: " + core.lgd.config.get("Legendary", "locale"))
        return core.lgd.config.get("Legendary", "locale").split("-")[0]
    else:
        logger.info("Found locale in system config: " + QLocale.system().name().split("_")[0])
        return QLocale.system().name().split("_")[0]


def get_possible_langs():
    langs = ["en"]
    for i in os.listdir(lang_path):
        if i.endswith(".qm"):
            langs.append(i.split(".")[0])
    return langs


def get_latest_version():
    try:
        resp = requests.get("https://api.github.com/repos/Dummerle/Rare/releases/latest")
        tag = json.loads(resp.content.decode("utf-8"))["tag_name"]
        return tag
    except requests.exceptions.ConnectionError:
        return "0.0.0"


def get_size(b: int) -> str:
    for i in ['', 'K', 'M', 'G', 'T', 'P', 'E']:
        if b < 1024:
            return f"{b:.2f}{i}B"
        b /= 1024


def create_desktop_link(app_name, core: LegendaryCore, type_of_link="desktop"):
    igame = core.get_installed_game(app_name)
    if os.path.exists(
            os.path.join(QSettings('Rare', 'Rare').value('img_dir', os.path.expanduser('~/.cache/rare/images'), str),
                         igame.app_name, 'Thumbnail.png')):
        icon = os.path.join(QSettings('Rare', 'Rare').value('img_dir', os.path.expanduser('~/.cache/rare/images'), str),
                            igame.app_name, 'Thumbnail.png')
    else:
        icon = os.path.join(QSettings('Rare', 'Rare').value('img_dir', os.path.expanduser('~/.cache/rare/images'), str),
                            igame.app_name, 'DieselGameBoxTall.png')
    # Linux
    if os.name == "posix":
        if type_of_link == "desktop":
            path = os.path.expanduser(f"~/Desktop/")
        elif type_of_link == "start_menu":
            path = os.path.expanduser("~/.local/share/applications/")
        else:
            return

        with open(f"{path}{igame.title}.desktop", "w") as desktop_file:
            desktop_file.write("[Desktop Entry]\n"
                               f"Name={igame.title}\n"
                               f"Type=Application\n"
                               f"Icon={icon}\n"
                               f"Exec=rare launch {app_name}\n"
                               "Terminal=false\n"
                               "StartupWMClass=rare-game\n"
                               )
        os.chmod(os.path.expanduser(f"~/Desktop/{igame.title}.desktop"), 0o755)

"""
Desktop app centered around the system tray icon.

Requires pystray:
    pip3 install pystray --user
"""

import os
import pystray
from PIL import Image

NAME = 'Eva'
PASSIVE_TEXT = 'Listen'
ACTIVE_TEXT = 'Stop Recording'
MIC_ON_ICO = os.path.abspath(os.path.dirname(__file__)) + '/mic_on.ico'
MIC_OFF_ICO = os.path.abspath(os.path.dirname(__file__)) + '/mic_off.ico'

def get_active_icon():
    return Image.open(MIC_ON_ICO)

def get_passive_icon():
    return Image.open(MIC_OFF_ICO)

def get_active_menu():
    menu_item = pystray.MenuItem(ACTIVE_TEXT, clicked)
    return pystray.Menu(menu_item)

def get_passive_menu():
    menu_item = pystray.MenuItem(PASSIVE_TEXT, clicked)
    return pystray.Menu(menu_item)

def clicked(icon):
    if icon.menu.items[0].text == PASSIVE_TEXT:
        icon.icon = get_active_icon()
        icon.menu = get_active_menu()
    else:
        icon.icon = get_passive_icon()
        icon.menu = get_passive_menu()

icon = pystray.Icon(name=NAME, icon=get_passive_icon(), title=NAME, menu=get_passive_menu())

def setup(icon):
    icon.visible = True

icon.run(setup)

"""
Desktop app centered around the system tray icon.

Requires pystray:
    pip3 install pystray --user
"""

import pystray
from PIL import Image

def get_active_icon():
    return Image.open('mic_on.ico')

def get_passive_icon():
    return Image.open('mic_off.ico')

def get_active_menu():
    menu_item = pystray.MenuItem('Stop Recording', clicked)
    return pystray.Menu(menu_item)

def get_passive_menu():
    menu_item = pystray.MenuItem('Listen', clicked)
    return pystray.Menu(menu_item)

def clicked(icon):
    if icon.menu.items[0].text == 'Listen':
        icon.icon = get_active_icon()
        icon.menu = get_active_menu()
    else:
        icon.icon = get_passive_icon()
        icon.menu = get_passive_menu()

icon = pystray.Icon(name='Eva', icon=get_passive_icon(), title='Eva', menu=get_passive_menu())

def setup(icon):
    icon.visible = True

icon.run(setup)

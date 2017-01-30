"""
A desktop client with a proper UI and taskbar icon is currently in the works.
The progress can be followed in the dev/desktop_client branch (help appreciated).
"""

import pystray
from PIL import Image

def get_active_icon():
    return Image.open('resources/mic_on.ico')

def get_passive_icon():
    return Image.open('resources/mic_off.ico')

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

def setup(icon):
    icon.visible = True

if __name__ == '__main__':
    icon = pystray.Icon(name='Eva', icon=get_passive_icon(), title='Eva', menu=get_passive_menu())
    icon.run(setup)

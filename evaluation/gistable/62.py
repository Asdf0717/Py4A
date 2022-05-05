#!/usr/bin/env python3
"""
Emulate Gnome's Unicode input method.

Requires `pyxhook` and `xdotool` to be installed

`pip install pyxhook`

`sudo apt-get install xdotool`
"""
import pyxhook
import subprocess
import string

held = set()
reading = False
numbers = []

def key_down(event):
    global held
    global reading
    global numbers
    if not reading:
        if event.Key.startswith('Control_'):
            held.add('Control')
        if event.Key.startswith('Shift_'):
            held.add('Shift')
        if event.Key == 'U':
            held.add('u')
        if held == {'Control', 'Shift', 'u'}:
            reading = True
            numbers = []
    else:
        if event.Key == 'space':
            reading = False
            # XXX: delete what was just typed. Ideally, I'd be able to cancel
            # the number keyboard events, but doing so is somewhat nonobvious
            args = ['BackSpace'] * (len(numbers) + 1) + ['U{}'.format(''.join(numbers))]
            subprocess.call(['xdotool', 'key', *args])
        elif event.Key in string.hexdigits:
            numbers.append(event.Key)

def key_up(event):
    global held
    global reading
    if held == {'Control', 'Shift', 'u'}:
        held.discard('Control')
    if event.Key.startswith('Shift_'):
        held.discard('Shift')
    if event.Key == 'U':
        held.discard('u')

if __name__ == '__main__':
    hookmgr = pyxhook.HookManager()
    hookmgr.KeyDown = key_down
    hookmgr.KeyUp = key_up
    hookmgr.HookKeyboard()
    hookmgr.start()

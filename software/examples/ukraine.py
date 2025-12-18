import sys
sys.path.insert(0, '..')
import time
from display import Display
from digit import Digit

# create display with 6 digits
display = Display()

# add 6 digits
for i in range(6):
    digit = Digit(i)
    display.extend(digit)

# slava ukraine
display.set_text("FCKPTN")


ua_flag = [
    (0xFF, 0xD7, 0x00),  # yellow
    (0xFF, 0xD7, 0x00),  # yellow
    (0xFF, 0xD7, 0x00),  # yellow
    (0x00, 0x78, 0xC8),  # blue
    (0x00, 0x78, 0xC8),  # blue
]

rainbow = [
    (0xFF, 0x00, 0x00),  # red
    (0xFF, 0x7F, 0x00),  # orange
    (0xFF, 0xFF, 0x00),  # yellow
    (0x00, 0xFF, 0x00),  # green
    (0x00, 0x00, 0xFF),  # blue
    (0x4B, 0x00, 0x82),  # indigo
    (0x8B, 0x00, 0xFF),  # violet
]

display.set_gradient_fg('h', ua_flag)

# flashing random fg and bg gradients
i = 0
while True:
    display.render()
    display.text_advance()
    time.sleep(.6)
    i += 1
    if i % 20 == 0:
        for _ in range(5):
            if i % 60 == 0:
                display.set_gradient_fg('h', rainbow)
            if i % 120 == 0:
                display.set_gradient_fg('v', rainbow)
            display.set_text("\xff\xff\xff\xff\xff\xff")
            display.render()
            time.sleep(0.1)
            display.set_text("      ")
            display.render()
            time.sleep(0.1)
        display.set_gradient_fg('h', ua_flag)
        display.set_text("YKPAIHA")
        if i % 60 == 0:
            display.set_text("FCKPTN")


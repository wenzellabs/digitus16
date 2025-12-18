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

gay_gradient = [
    (0xFF, 0x00, 0x00),  # Red
    (0xFF, 0x80, 0x00),  # Orange
    (0xFF, 0xFF, 0x00),  # Yellow
    (0x00, 0xFF, 0x00),  # Green
    (0x00, 0xFF, 0xFF),  # Cyan
    (0x00, 0x00, 0xFF),  # Blue
    (0x80, 0x00, 0xFF)   # Purple/Violet
]

trans_gradient = [
    (0x00, 0x80, 0xFF),  # Bright blue
    (0xFF, 0xFF, 0xFF),  # Pure white
    (0xFF, 0x00, 0x80),  # Hot pink
    (0x00, 0x80, 0xFF),  # Bright blue
    (0xFF, 0xFF, 0xFF),  # Pure white
    (0xFF, 0x00, 0x80),  # Hot pink
    (0x00, 0x80, 0xFF)   # Bright blue
]

# flashing random fg and bg gradients
while True:
    # all leds lit
    display.set_text("\xff\xff\xff\xff\xff\xff")
    for _ in range(33):
        trans_gradient = trans_gradient[1:] + trans_gradient[:1]
        display.set_gradient_fg('V', trans_gradient)
        display.render()
        time.sleep(0.1)
    for _ in range(33):
        gay_gradient = gay_gradient[1:] + gay_gradient[:1]
        display.set_gradient_fg('V', gay_gradient)
        display.render()
        time.sleep(0.1)
    for _ in range(33):
        display.set_text("be gay")
        gay_gradient = gay_gradient[1:] + gay_gradient[:1]
        display.set_gradient_fg('V', gay_gradient)
        display.render()
        time.sleep(0.1)

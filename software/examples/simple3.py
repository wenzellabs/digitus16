import sys
sys.path.insert(0, '..')
import time
import random
from display import Display
from digit import Digit

# create display with 6 digits
display = Display()

# add 6 digits
for i in range(6):
    digit = Digit(i)
    display.extend(digit)

# a text
display.set_text("random")

# animate text by advancing text every second
while True:
    r=random.randint(0, 0xff)
    g=random.randint(0, 0xff)
    b=random.randint(0, 0xff)
    display.set_fg((r,g,b))
    display.set_bg((0xff - r, 0xff - g, 0xff - b))
    display.render()
    time.sleep(0.3)

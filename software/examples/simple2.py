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

# a text too long for the display
display.set_text("my second simple example")

# animate text by advancing text every second
while True:
    display.text_advance()
    display.render()
    time.sleep(1)

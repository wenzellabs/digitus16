import sys
sys.path.insert(0, '..')
from display import Display
from digit import Digit

# create display with 6 digits
display = Display()

display.set_brightness(31)

# add 6 digits
for i in range(6):
    digit = Digit(i)
    display.extend(digit)

display.set_text("\xff\xff\xff\xff\xff\xff")
display.render()
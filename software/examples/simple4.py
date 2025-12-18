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

# more a pattern than a text
display.set_text("   \xff\xff\xff")


# flashing random fg and bg gradients
while True:
    random_colors_fg = [
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF))
    ]
    random_colors_bg = [
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF)),
        (random.randint(0, 0xFF), random.randint(0, 0xFF), random.randint(0, 0xFF))
    ]

    display.set_gradient_fg('h', random_colors_fg)
    display.set_gradient_bg('h', random_colors_bg)
    display.render()
    time.sleep(1)

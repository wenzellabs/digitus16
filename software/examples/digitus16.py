import sys
sys.path.insert(0, '..')
import time
from display import Display
from digit import Digit

print("Digitus16 Rainbow Scrolling Demo")

# Create display with 6 digits
display = Display()

# Add 6 digits
for i in range(6):
    digit = Digit(i)
    display.extend(digit)

display.set_brightness(3)

# Set the scrolling text
scroll_text = "this is digitus16"
display.set_text(scroll_text)

# Rainbow colors for foreground
rainbow_colors = [
    (0xFF, 0x00, 0x00),  # Red
    (0xFF, 0x80, 0x00),  # Orange
    (0xFF, 0xFF, 0x00),  # Yellow
    (0x00, 0xFF, 0x00),  # Green
    (0x00, 0xFF, 0xFF),  # Cyan
    (0x00, 0x00, 0xFF),  # Blue
    (0x80, 0x00, 0xFF)   # Purple/Violet
]

# Set colors
display.set_gradient_fg('x', rainbow_colors)  # Rainbow horizontally
display.set_bg((0x00, 0x00, 0x00))            # Black background

try:
    while True:
        display.render()
        time.sleep(0.5)
        display.text_advance(bounce=True)

except KeyboardInterrupt:
    print("\nStopping demo...")
    # Turn off all LEDs
    display.set_fg((0x00, 0x00, 0x00))
    display.set_bg((0x00, 0x00, 0x00))
    display.render()

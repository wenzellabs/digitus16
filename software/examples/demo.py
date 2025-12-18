import sys
sys.path.insert(0, '..')
import display
import digit
import time

d=display.Display()

for i in range(6):
    dd=digit.Digit(i)
    d.extend(dd)

d.set_brightness(8)

d.set_fg((250, 250, 250))
d.set_bg((5, 7, 15))

name=[
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]

gay_gradient = [
    (0xFF, 0x00, 0x00),  # Red
    (0xFF, 0x80, 0x00),  # Orange
    (0xFF, 0xFF, 0x00),  # Yellow
    (0x00, 0xFF, 0x00),  # Green
    (0x00, 0xFF, 0xFF),  # Cyan
    (0x00, 0x00, 0xFF),  # Blue
    (0x80, 0x00, 0xFF)   # Purple/Violet
]

for i in range(1, 10):
    d.set_text(f"{i}{name[i]}")
    d.set_bg((5//i, 7//i, 15//i))
    d.render()
    time.sleep(0.4)

d.set_text('\xff\xff\xff\xff\xff\xff')
d.render()

for i in range(10,0,-1):
    d.set_brightness(2*i)
    d.render()
    time.sleep(0.1)

d.set_brightness(1)
d.set_text('XXXXXX')
d.render()

for _ in range(3):
    for col in range(0, 256, 16):
        d.set_fg((col, 0, 0))
        d.render()
    for col in range(0, 256, 16):
        d.set_fg((0, col, 0))
        d.render()
    for col in range(0, 256, 16):
        d.set_fg((0, 0, col))
        d.render()

    for col in range(0, 256, 16):
        d.set_bg((col, 0, 0))
        d.render()
    for col in range(0, 256, 16):
        d.set_bg((0, col, 0))
        d.render()
    for col in range(0, 256, 16):
        d.set_bg((0, 0, col))
        d.render()

d.set_brightness(8)
d.set_text(" TEXT ")
d.set_gradient_fg('h', [
    (0xff, 0x00, 0x00),
    (0xff, 0x7f, 0x00),
    (0xff, 0xff, 0x80),
])
d.set_gradient_bg('h', [
    (0xff, 0x00, 0x00),
    (0xff, 0x7f, 0x00),
    (0xff, 0xff, 0x80),
])
d.render()
time.sleep(2)

for i in range(1, 0xff, 16):
    d.set_gradient_bg('h', [
        (0xff//i, 0x00//i, 0x00//i),
        (0xff//i, 0x7f//i, 0x00//i),
        (0xff//i, 0xff//i, 0x80//i),
    ])
    d.render()
    time.sleep(0.2)
time.sleep(1)

for i in range(0xff, 1, -15):
    d.set_gradient_bg('h', [
        (0xff//i, 0x00//i, 0x00//i),
        (0xff//i, 0x7f//i, 0x00//i),
        (0xff//i, 0xff//i, 0x80//i),
    ])
    d.render()
    time.sleep(0.1)
time.sleep(2)

d.set_text(" red. ")
d.set_fg((0xff, 0x00, 0x00))
d.set_bg((0xff, 0xff, 0xff))
d.render()
for i in range(0xff, -1, -15):
    d.set_bg((i, i, i))
    d.render()
    time.sleep(0.2)
time.sleep(2)

d.set_text("green.")
d.set_fg((0x00, 0xff, 0x00))
d.set_bg((0x00, 0x00, 0x00))
d.render()
time.sleep(2)

d.set_text(" blue.")
d.set_fg((0x00, 0x00, 0xff))
d.render()
time.sleep(2)

d.set_text("\xffgrad\xff")

d.set_gradient_fg('y', [
    (0xff, 0xff, 0x00),
    (0xff, 0xff, 0x00),
    (0xff, 0xff, 0x00),
    (0x00, 0x00, 0xff),
    (0x00, 0x00, 0xff)
])
d.render()
time.sleep(3)

d.set_gradient_fg('H', [
    (0xff, 0x00, 0),
    (0x00, 0x00, 0xff),
    (0x00, 0xff, 0)])
d.render()
time.sleep(3)

d.set_gradient_fg('x', gay_gradient)
d.render()
time.sleep(3)

d.set_gradient_fg('h', [
    (0x00, 0x1f, 0x1f),
    (0x1f, 0x1f, 0x00),
    (0x1f, 0x00, 0x1f),
])
d.render()
time.sleep(3)

d.set_text(" done ")
#d.set_fg((0xff, 0xff, 0xff))
d.set_fg((0x00, 0x00, 0x00))
d.set_gradient_bg('H', gay_gradient)
d.render()

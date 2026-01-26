# digitus16

digitus16 is a 16-segment RGB display.

it comes as single digit or up to six digits on a single PCB. software-wise many more columns and rows can be combined.

comes with a 3d-printed screen and interconnect boards to simplify combining 2, 4 or 6 digits to a larger display.

there's an optional screen from PCB material with nice gold edged segments.

the single digit or whole display is controlled through a simple 2-wire SPI interface and can be hooked up to pretty much any microcontroller.

![digitus16 in rainbow animation](pic/digitus16.gif)

# examples

see the [`software/examples/`](software/examples/) subfolder for the code

<hr>

- simple1:

![simple1](pic/simple1.gif)

<hr>

- simple2:

![simple2](pic/simple2.gif)

<hr>

- simple3:

![simple3](pic/simple3.gif)

<hr>

- simple4:

![simple4](pic/simple4.gif)

<hr>

- simple5:

![simple5](pic/simple5.gif)

<hr>

- seasons:

![seasons](pic/seasons.gif)

<hr>

- temperature:

![temperature](pic/temperature.gif)

<hr>

- demo:

![demo](pic/demo.gif)

<hr>

# software

see the [`software/`](software/) subfolder

there is software/firmware support for
- micropython on the **ESP32** (and variants)
- micropython on the **Raspberry Pi Pico** (and variants)
- python on **linux** (Raspberry Pi and others, basically any linux with a /dev/spiX.Y)

there's software support for
- fonts
- scrolltext
- gradients
- foreground and background colors
- multicolumn multirow arrangements for larger assemblies of digits

there's planned software support for
- images using voronoi patterns (esp. for larger arrangements of digits)
- using the assembly of digits as image framebuffer

## programming

for now, just see the [`software/examples/`](software/examples/) subfolder

# hardware

## what you get
kit's content (top to bottom):

- 3d-printed bezel and diffusor

- main PCB with 6 digits of 16 SPI addressable RGB LEDs each

- 4-pin main male connector for power and SPI signals

- 4-pin main female connector for power and SPI signals

![digitus16x6 kit](pic/digitus16x6_kit.jpg)

various assemblies are feasible. most will be a sandwich of the bare PCB and a 3d-printed bezel and diffusor. we've also successfully used bezels that were laser-cut from wood or PMMA (although PMMA becomes very brittle with the thin structures). Or paper, wood or other materials can be used as yet another diffusor and to have a uniform clean surface.

## mechanical

- display height: 26.7mm
- display height center: 24.5mm
- display width: 106.7mm
- display thickness: 5.0mm (PCB + 3d-printed bezel and diffusor)

see the [`3d/`](3d/) subfolder for 3D models.

front view:

![digitus16x6 front](pic/digitus16x6_front.png)

back view:

![digitus16x6 back](pic/digitus16x6_back.png)

## electrical interface

- 5V power supply in
- GND
- SPI clock in **CI** (3.3V level or 5V level)
- SPI data in **DI** (3.3V level or 5V level)
- optional:
    - 5V power supply out
    - GND
    - SPI clock out **CO** (5V level)
    - SPI data out **DO** (5V level)

## current/power

absolute maximum current / power @5V, all LEDs 100% white, full brightness: 485mA / 2.425W

maximum current / power @5V, all LEDs 100% white, recommended maxiumum brightness (15 of 31): 280mA / 1.4W

the LEDs have a brightness setting 0-31. we recommend you only drive the LEDs up to a maxiumum brightness level of 15, otherwise you get the self-explanatory warning from the API:
```
>>> display.set_brightness(31)
setting high brightness values is not recommended due to reduced LED lifetime!
```

## assembly guide

remove the 3d-printed bezel and diffusor before soldering.

solder the four pins for the 5V and data connection to the main PCB, either vertical to the back, or flat to the bottom, according to your mounting requirements.

the pinout is documented on the backside of the PCB. see also the photo above.

only after all soldering is done snap the 3d-printed bezel and diffusor back on the main pcb. it should clip on firmly, and glueing is possible but probably not necessary.

## why SK9822/APA102 and not WS2812B flavoured RGB LEDs

we use SPI-based SK9822/APA102 and not the more widely used WS2812B flavoured RGB LEDs which require only one pin instead of two (aside from power). here are the reasons why we try to avoid WS2812B flavoured RGB LEDs whenever possible:

- WS2812B require precise timing
- WS2812B only come with an internal RC oscillator which is not very stable, especially over temperatures. there's no way to accurately drive WS2812B over wide temperature ranges
- WS2812B require bitbanging. the timing has to be granted in SW/FW since there's no special WS2812B HW unit on MCUs
- to keep the timing all other interrupts must be disabled on the MCU
- disabling interrupts can mean loosing other events on the MCU, e.g. you start loosing button presses or keystrokes on the UART
- SK9822s or APA102s come with an extra line, that is clock, the advantage is that the SW/FW can run them fast or slow or even pause the transmission, e.g. during high prio interrupts
- most MCUs have a dedicated SPI master controler HW integrated, that means no bitbanging from SW
- if you have an RTOS like FreeRTOS the RGB LED task doesn't need the highest priority/disable the interrupts anymore, and you won't miss CAN-frames while you render that mmeeoww on the screen

end-of-WS2812B-rant


import sys
sys.path.insert(0, '..')
import random
import time
from display import Display
from digit import Digit

TEXT = "TEXT"
RAIN = "RAIN"
TEMP = "TEMP"
TIME = "TIME"

# Each row is (duration in seconds, mode, optional mode value).
ANIMATION = [
    (0.2, TEXT, "\xff\xff\xff\xff\xff\xff"),
    (1, TEXT, "      "),
    (0.4, RAIN, None),
    (0.5, TEXT, " \xff \xff \xff"),
    (0.5, TEXT, "\xff \xff \xff "),
    (3.3, TIME, None),
    (2, TEMP, -2),
    (1, TEXT, "HELLO "),
    (1, TEXT, " WEEN "),
    (1, TEXT, "      "),
    (2, TEXT, "SPOOOK"),
    (0.2, TEXT, " PUKE "),
    (1, TEXT, "      "),
    (2, TEXT, "HORROR"),
    (1, TEXT, "      "),
    (2, TEXT, "scary "),
    (2, TEXT, "spider"),
    (1, TEXT, "      "),
    (2, TEXT, "PUMPKN"),
    (1, TEXT, "      "),
    (2, TEXT, "CANDY "),
    (1, TEXT, "      "),
    (2, TEXT, "GHOSTS"),
    (1, TEXT, "      "),
    (2, TEXT, "BLOOD "),
    (1, TEXT, "      "),
    (2, TEXT, "Witch "),
    (1, TEXT, "      "),
    (2, TEXT, "Zombie"),
    (1, TEXT, "      "),
]

DIGIT_COUNT = 6
PIN_TEMP = 10
PIN_SDA = 8
PIN_SCL = 9

ORANGE = (0xFF, 0x50, 0x00)
GREEN = (0x00, 0x20, 0x00)


display = Display()
for i in range(DIGIT_COUNT):
    display.extend(Digit(i))
display.set_brightness(8)
display.set_fg(ORANGE)
display.set_bg(GREEN)

rtc_i2c = None
temp_sensor = None
temp_device = None
rainbow_offset = 0


def init_rtc():
    global rtc_i2c
    import machine
    rtc_i2c = machine.I2C(
        0,
        scl=machine.Pin(PIN_SCL),
        sda=machine.Pin(PIN_SDA),
        freq=100000
    )


def init_temperature():
    global temp_sensor, temp_device
    import machine
    import onewire
    import ds18x20
    temp_sensor = ds18x20.DS18X20(onewire.OneWire(machine.Pin(PIN_TEMP)))
    devices = temp_sensor.scan()
    if not devices:
        raise RuntimeError("No DS18B20 found on GPIO{}".format(PIN_TEMP))
    temp_device = devices[0]
    print("Found DS18B20 on GPIO{}".format(PIN_TEMP))


def bcd_to_decimal(value):
    return ((value >> 4) * 10) + (value & 0x0F)


def get_time_text():
    """Read DS1307 time, falling back to the system clock."""
    if rtc_i2c is not None:
        try:
            data = rtc_i2c.readfrom_mem(0x68, 0x00, 3)
            seconds = bcd_to_decimal(data[0] & 0x7F)
            minutes = bcd_to_decimal(data[1])
            hours = bcd_to_decimal(data[2] & 0x3F)
            return "{:02d}{:02d}{:02d}".format(hours, minutes, seconds)
        except Exception:
            pass
    current_time = time.localtime()
    return "{:02d}{:02d}{:02d}".format(
        current_time[3], current_time[4], current_time[5]
    )


def read_temperature():
    temp_sensor.convert_temp()
    time.sleep_ms(750)
    return temp_sensor.read_temp(temp_device)


def hue_to_rgb(hue):
    h = (hue % 360) / 60.0
    sector = int(h)
    fraction = h - sector
    rising = int(255 * fraction)
    falling = int(255 * (1 - fraction))
    if sector == 0:
        return (255, rising, 0)
    if sector == 1:
        return (falling, 255, 0)
    if sector == 2:
        return (0, 255, rising)
    if sector == 3:
        return (0, falling, 255)
    if sector == 4:
        return (rising, 0, 255)
    return (255, 0, falling)


def show_rainbow():
    global rainbow_offset
    colors = []
    for index in range(DIGIT_COUNT):
        hue = rainbow_offset + index * 360 / max(1, DIGIT_COUNT - 1)
        colors.append(hue_to_rgb(hue))
    display.set_text("\xff" * DIGIT_COUNT)
    display.set_gradient_fg('x', colors)
    rainbow_offset = (rainbow_offset + 8) % 360


def show_temperature(offset):
    temperature = read_temperature()
    display.set_fg(ORANGE)
    if temperature is None:
        display.set_text("NO TMP")
    else:
        adjusted_temperature = temperature + offset
        display.set_text("{:5.1f}C".format(adjusted_temperature))


def show_animation_step(duration, mode, value):
    if mode == TEXT:
        display.set_fg(ORANGE)
        display.set_text(value)
    elif mode == TEMP:
        show_temperature(value)
    elif mode not in (RAIN, TIME):
        raise ValueError("Unknown animation mode: {}".format(mode))

    started = time.ticks_ms()
    duration_ms = int(duration * 1000)
    while time.ticks_diff(time.ticks_ms(), started) < duration_ms:
        if mode == RAIN:
            show_rainbow()
        elif mode == TIME:
            display.set_fg(ORANGE)
            display.set_text(get_time_text())
        if random.random() < 0.2:
            display.twinkle()
        display.render()
        time.sleep_ms(100)


def main():
    init_rtc()
    init_temperature()
    while True:
        for duration, mode, value in ANIMATION:
            show_animation_step(duration, mode, value)


if __name__ == "__main__":
    main()

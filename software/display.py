
from digit import Digit
import sys

class Layer:
    FG = "foreground"
    BG = "background"

class Display:
    def __init__(self):

        self.elements = []
        self.digits = []
        self.ordered_leds = []
        self.digit_count = 0

        self.x_display = 0
        self.y_display = 0
        self.x_items = 0
        self.y_items = 0
        self.x_cursor = 0
        self.y_cursor = 0

        self.mode = 'alphanum'  # or 'raw'

        self.text = ''
        self.text_anim_direction = 'left'  # or 'right'
        self.text_render_index = 0

        self.brightness = 2 # 0 (off) to 31

        # SPI configuration (default values, will be set per platform)
        self.spi_baudrate = 4000000
        plat = sys.platform
        if plat == "rp2":
            # Pi Pico: GP2=SCK, GP3=MOSI
            self.spi_n = 0
            self.spi_sck = 2
            self.spi_mosi = 3
        elif plat == "esp32":
            # ESP32: D8=SCK, D10=MOSI (user specified)
            # On ESP32, pins are usually specified by GPIO number, e.g. D8=8, D10=10
            self.spi_n = 1
            self.spi_sck = 4
            self.spi_mosi = 6
        elif plat.startswith("linux"):
            # Linux systems (including Raspberry Pi): use spidev
            self.spi_bus = 0  # Default SPI bus number
            self.spi_device = 0  # Default SPI device number
            self.set_linux_spi_dev_path(f"/dev/spidev{self.spi_bus}.{self.spi_device}")
        else:
            print(f"Unsupported platform '{sys.platform}' for SPI pin mapping")

    def set_spi(self, n: int):
        self.spi_n = n

    def set_sck(self, pin: int):
        self.spi_sck = pin

    def set_mosi(self, pin: int):
        self.spi_mosi = pin

    def set_spi_baudrate(self, baudrate: int):
        self.spi_baudrate = baudrate

    def set_linux_spi_dev_path(self, path: str):
        self.spi_dev_path = path

    def extend(self, LED_obj, direction='horizontal'):
        self.elements.append(LED_obj)
        if isinstance(LED_obj, Digit):
            self.digit_count += 1
            self.digits.append(LED_obj)

        self.ordered_leds += LED_obj.get_leds()

        if direction == 'horizontal':
            if self.x_cursor == 0 and self.y_cursor == 0: # first entry
                self.x_items += 1
                self.y_items += 1
                self.x_cursor += 1
                self.y_cursor += 1
                self.x_display += LED_obj.get_width()
                self.y_display += LED_obj.get_height()
            else:
                if self.x_cursor >= self.x_items: # are we widening?
                    self.x_cursor += 1
                    self.x_items += 1
                    self.x_display += LED_obj.get_width()
                else:
                    self.x_cursor += 1
            if isinstance(LED_obj, Digit):
                LED_obj.extend_horiz(self.x_cursor-1)
        elif direction == 'vertical':
            if self.x_cursor == 0 and self.y_cursor == 0: # first entry
                self.x_items += 1
                self.y_items += 1
                self.x_cursor += 1
                self.y_cursor += 1
                self.x_display += LED_obj.get_width()
                self.y_display += LED_obj.get_height()
            else:
                if self.y_cursor >= self.y_items: # are we raising?
                    self.y_cursor += 1
                    self.y_items += 1
                    self.y_display += LED_obj.get_height()
                else:
                    self.y_cursor += 1
            if isinstance(LED_obj, Digit):
                LED_obj.extend_vert(self.y_cursor-1)

    def get_cursor(self):
        return self.x_cursor, self.y_cursor

    def set_cursor(self, x: int, y: int):
        self.x_cursor = x
        self.y_cursor = y

    def get_dimensions(self):
        return self.x_display, self.y_display

    def get_int_dimensions(self):
        return self.x_items, self.y_items

    def get_aspect_ratio(self):
        return self.x_display / self.y_display if self.y_display != 0 else 0

    def turn_digit_on(self, n):
        if 0 <= n < self.digit_count:
            self.digits[n].turn_on()

    def turn_digit_off(self, n):
        if 0 <= n < self.digit_count:
            self.digits[n].turn_off()

    def turn_all_digits_off(self):
        for digit in self.digits:
            digit.turn_off()

    def turn_all_digits_on(self):
        for digit in self.digits:
            digit.turn_on()

    def set_mode(self, mode):
        assert mode in ['alphanum', 'raw']
        self.mode = mode

    def get_state(self):
        return {
            'mode': self.mode,
            'digits': [digit.get_state() for digit in self.digits],
        }

    def set_text(self, text, direction='left'):
        self.text = text
        self.text_anim_direction = direction
        self.text_render_index = 0

    def set_number(self, number, direction='left'):
        num_str = str(number)
        # Right-align by adding leading spaces if needed
        if len(num_str) < self.digit_count:
            num_str = ' ' * (self.digit_count - len(num_str)) + num_str
        self.set_text(num_str, direction)

    def text_advance(self, bounce=True):
        """
        Advance the text scroll position.
        If bounce is True, text bounces at ends (back and forth).
        If bounce is False, text scrolls left and repeats from the start.
        """
        max_index = max(0, len(self.text) - self.digit_count)
        pause_ticks = 3
        if not hasattr(self, '_pause_counter'):
            self._pause_counter = 0
        if bounce:
            if self.text_anim_direction == 'left':
                if self.text_render_index < max_index:
                    self.text_render_index += 1
                    self._pause_counter = 0
                else:
                    if self._pause_counter < pause_ticks:
                        self._pause_counter += 1
                    else:
                        self.text_anim_direction = 'right'
                        self._pause_counter = 0
            elif self.text_anim_direction == 'right':
                if self.text_render_index > 0:
                    self.text_render_index -= 1
                    self._pause_counter = 0
                else:
                    if self._pause_counter < pause_ticks:
                        self._pause_counter += 1
                    else:
                        self.text_anim_direction = 'left'
                        self._pause_counter = 0
        else:
            # Only scroll left, repeat from start
            if self.text_render_index < max_index:
                self.text_render_index += 1
            else:
                self.text_render_index = 0

    def set_brightness(self, b:int):
        if b < 0 or b > 31:
            print(f'brightness {b} out of range. must be between 0 and 31')
            return
        if b > 15:
            print('setting high brightness values is not recommended due to reduced LED lifetime!')
        self.brightness = b

    def render(self):
        self.text_render()

    def set_char(self, index: int, char: str):
        if 0 <= index < self.digit_count:
            self.digits[index].turn_off()
            self.digits[index].set_char(char)

    def text_render(self):
        if len(self.text) > 0:
            for element in self.elements:
                element.turn_off()
            # Only display the substring starting at self.text_render_index
            start = self.text_render_index
            end = start + self.digit_count
            visible = self.text[start:end]
            # Pad or trim to digit_count (MicroPython: no ljust)
            if len(visible) < self.digit_count:
                visible = visible + ' ' * (self.digit_count - len(visible))
            else:
                visible = visible[:self.digit_count]
            for i in range(self.digit_count):
                self.digits[self.digit_count - 1 - i].set_char(visible[i])

        def led_to_sk9822_bytes(led):
            state = led.get_color()
            r, g, b = state
            return bytes([0b11100000 | self.brightness, b, g, r])

        # SK9822 protocol:
        # start frame (4x0x00)
        # LED frames
        # end frame (4x0xFF), but more seem required for EF
        start_frame = b'\x00' * 4
        end_frame = b'\xff' * 8

        led_frames = b''.join([led_to_sk9822_bytes(led) for led in self.ordered_leds])
        spi_data = start_frame + led_frames + end_frame

        def hexdump(spi_data):
            # Nicer hexdump: 4 bytes per line
            print(f'SPI Data Length: {len(spi_data)} the bytes:')
            count = 0
            for i in range(0, len(spi_data), 4):
                chunk = spi_data[i:i+4]
                count += 1
                print(f'{count} ', end='')
                print(' '.join(f'{b:02X}' for b in chunk))

        # hexdump(spi_data)

        # --- SK9822 SPI output ---
        try:
            import machine
            # MicroPython platforms (Pi Pico, ESP32)
            if sys.platform == "rp2":
                spi = machine.SPI(
                    self.spi_n,
                    baudrate=self.spi_baudrate,
                    polarity=0,
                    phase=0,
                    sck=machine.Pin(self.spi_sck),
                    mosi=machine.Pin(self.spi_mosi)
                )
            elif sys.platform == "esp32":
                spi = machine.SPI(
                    self.spi_n,
                    baudrate=self.spi_baudrate,
                    polarity=0,
                    phase=0,
                    sck=machine.Pin(self.spi_sck),
                    mosi=machine.Pin(self.spi_mosi)
                )
            else:
                print("Unsupported MicroPython platform for SPI setup")
                return
            spi.write(spi_data)

        except ImportError:
            # Not running on MicroPython, try Linux spidev
            if sys.platform.startswith("linux"):
                try:
                    import spidev
                    spi = spidev.SpiDev()
                    spi.open(self.spi_bus, self.spi_device)

                    # Configure SPI parameters
                    spi.max_speed_hz = self.spi_baudrate
                    spi.mode = 0  # SPI mode 0 (CPOL=0, CPHA=0)

                    # Write data to SPI
                    spi.writebytes(list(spi_data))
                    spi.close()

                except ImportError:
                    print("SK9822 output: spidev module not found. Install with: pip install spidev")
                    return
                except PermissionError:
                    print(f"SK9822 output: Permission denied accessing {self.spi_dev_path}. Try running with sudo or add user to spi group.")
                    return
                except FileNotFoundError:
                    print(f"SK9822 output: SPI device {self.spi_dev_path} not found. Check if SPI is enabled.")
                    return
                except Exception as e:
                    print(f"SK9822 output: SPI error - {e}")
                    return
            else:
                print(f"SK9822 output: Unsupported platform '{sys.platform}' - no machine module or spidev support")
                return


    def set_layer(self, color, layer: Layer=Layer.FG):
        for element in self.elements:
            if layer == Layer.FG:
                element.set_fg(color)
            elif layer == Layer.BG:
                element.set_bg(color)

    def set_fg(self, color):
        self.set_layer(color, layer=Layer.FG)

    def set_bg(self, color):
        self.set_layer(color, layer=Layer.BG)

    def set_digit_layer(self, index:int, color, layer: Layer=Layer.FG):
        if 0 <= index < self.digit_count:
            if layer == Layer.FG:
                self.digits[index].set_fg(color)
            elif layer == Layer.BG:
                self.digits[index].set_bg(color)

    def set_digit_fg(self, index:int, color):
        self.set_digit_layer(index, color, layer=Layer.FG)

    def set_digit_bg(self, index:int, color):
        self.set_digit_layer(index, color, layer=Layer.BG)

    def set_rainbow_fg(self):
        self.set_rainbow_layer(layer=Layer.FG)

    def set_rainbow_bg(self):
        self.set_rainbow_layer(layer=Layer.BG)

    def set_rainbow_layer(self, layer: Layer=Layer.FG):
        """Set all LED foreground colors to a rainbow pattern."""
        n = len(self.ordered_leds)
        def wheel(pos):
            if pos < 85:
                return (pos * 3, 255 - pos * 3, 0)
            elif pos < 170:
                pos -= 85
                return (255 - pos * 3, 0, pos * 3)
            else:
                pos -= 170
                return (0, pos * 3, 255 - pos * 3)
        for i, led in enumerate(self.ordered_leds):
            color = wheel(int(i * 256 / n) & 255)
            if layer == Layer.FG:
                led.set_fg(color)
            elif layer == Layer.BG:
                led.set_bg(color)

    def shift_layer(self, amount=1, layer: Layer=Layer.FG):
        if layer == Layer.FG:
            self.shift_fg(amount)
        elif layer == Layer.BG:
            self.shift_bg(amount)

    def shift_fg(self, amount=1):
        """Rotate all LED foreground colors by amount (default 1)."""
        n = len(self.ordered_leds)
        if n == 0 or amount % n == 0:
            return
        # Get current colors
        colors = [led.get_fg_color() for led in self.ordered_leds]
        # Rotate
        amount = amount % n
        colors = colors[-amount:] + colors[:-amount]
        # Set back
        for led, color in zip(self.ordered_leds, colors):
            led.set_fg(color)

    def shift_bg(self, amount=1):
        """Rotate all LED background colors by amount (default 1)."""
        n = len(self.ordered_leds)
        if n == 0 or amount % n == 0:
            return
        # Get current colors
        colors = [led.get_bg_color() for led in self.ordered_leds]
        # Rotate
        amount = amount % n
        colors = colors[-amount:] + colors[:-amount]
        # Set back
        for led, color in zip(self.ordered_leds, colors):
            led.set_bg(color)

    def set_all_layer_leds(self, colors, layer: Layer=Layer.FG):
        if layer == Layer.FG:
            self.set_all_fg_leds(colors)
        elif layer == Layer.BG:
            self.set_all_bg_leds(colors)

    def set_all_bg_leds(self, colors):
        """
        Set all LEDs' colors from a list of (r, g, b) tuples.
        colors: list of (r, g, b), one per LED in self.ordered_leds
        """
        for led, color in zip(self.ordered_leds, colors):
            led.set_bg(color)

    def set_all_fg_leds(self, colors):
        """
        Set all LEDs' colors from a list of (r, g, b) tuples.
        colors: list of (r, g, b), one per LED in self.ordered_leds
        """
        for led, color in zip(self.ordered_leds, colors):
            led.set_fg(color)

    def set_gradient_bg(self, axis, colors):
        self.set_gradient_layer(axis, colors, layer=Layer.BG)

    def set_gradient_fg(self, axis, colors):
        self.set_gradient_layer(axis, colors, layer=Layer.FG)

    def set_gradient_layer(self, axis, colors, layer: Layer=Layer.FG):
        """
        Set a gradient of FG/BG colors along the given axis ('x' or 'y') using the provided list of (r,g,b) colors.
        LEDs are sorted by axis, and colors are linearly interpolated between the given colors.
        """
        assert axis in ('x', 'X', 'v', 'V', 'y', 'Y', 'h', 'H'), "axis must be 'x' or 'v' or 'y' or 'h'"
        if axis in ('X', 'v', 'V'):
            axis = 'x'
        n = len(self.ordered_leds)
        if n == 0 or len(colors) < 2:
            return
        # Get LED positions and group by position
        if axis == 'x':
            led_positions = {}
            for i, led in enumerate(self.ordered_leds):
                pos = led.get_x()
                if pos not in led_positions:
                    led_positions[pos] = []
                led_positions[pos].append(i)
        else:
            led_positions = {}
            for i, led in enumerate(self.ordered_leds):
                pos = led.get_y()
                if pos not in led_positions:
                    led_positions[pos] = []
                led_positions[pos].append(i)

        # Sort unique positions
        unique_positions = sorted(led_positions.keys())
        num_positions = len(unique_positions)

        if num_positions == 0:
            return

        # Calculate gradient colors for each unique position
        num_segments = len(colors) - 1
        for pos_idx, pos in enumerate(unique_positions):
            # Find which segment this position is in
            seg = int(pos_idx * num_segments / max(1, num_positions - 1))
            seg = min(seg, num_segments - 1)

            if num_positions == 1:
                t = 0
            else:
                t = pos_idx / (num_positions - 1) * num_segments - seg
                t = max(0, min(1, t))

            c0 = colors[seg]
            c1 = colors[min(seg + 1, len(colors) - 1)]
            r = int(c0[0] + (c1[0] - c0[0]) * t)
            g = int(c0[1] + (c1[1] - c0[1]) * t)
            b_ = int(c0[2] + (c1[2] - c0[2]) * t)
            color = (r, g, b_)

            # Apply the same color to all LEDs at this position
            for led_idx in led_positions[pos]:
                led = self.ordered_leds[led_idx]
                if layer == Layer.FG:
                    led.set_fg(color)
                elif layer == Layer.BG:
                    led.set_bg(color)

#!/usr/bin/env python3
"""
Blonkenclick - ESP32 Multi-Mode Clock Application
Displays time, text, and battery voltage on digitus16 display
Optimized for ESP32 with fallbacks for other platforms
"""

import os
import sys
import time

sys.path.insert(0, '..')
from display import Display
from digit import Digit

# ============================================================================
# SETTINGS SECTION
# ============================================================================

# Display Configuration
DIGIT_COUNT = 6  # Number of digits to display
USE_SECONDS = True  # Display seconds in time mode
BLINK_COLON = True  # Blink the colon separator
FORMAT_24H = True  # True for 24h format, False for 12h format
RAINBOW_NUMBERS = True  # Rainbow colored numbers based on time values

# Temperature Configuration
USE_FAHRENHEIT = False  # True for Fahrenheit, False for Celsius

# Timing Configuration
CYCLE_TIME = 9876  # Time in milliseconds to display each mode
LOOP_DELAY_MS = 100  # Main loop delay in milliseconds for display refresh rate
AUTO_BRIGHTNESS = True  # Enable automatic brightness based on LDR

# Text Display Configuration
CYCLE_TEXT = [
    "->39C3",
    "Power",
    "Cycles",
    "      ",
    "\xff\xff\xff\xff\xff\xff",
    " this ",
    "  is  ",
    "blonke",
    "nclick",
]

# ESP32 Hardware Pin Configuration
PIN_LDR = 0  # GPIO0 (A0) - Light Dependent Resistor for brightness
PIN_BAT_RTC = 3  # GPIO3 (A3) - RTC battery voltage monitoring
PIN_SDA = 8  # GPIO8 - I2C SDA for RTC
PIN_SCL = 9  # GPIO9 - I2C SCL for RTC
PIN_TEMP = 10  # GPIO10 - DS18B20 temperature sensor

# ============================================================================
# DISPLAY_ITEMS ARRAY
# ============================================================================

DISPLAY_ITEMS = [
    {
        'key': 'TIME',
        'init_func': 'init_time',
        'func': 'display_time'
    },
    {
        'key': 'TEMP',
        'init_func': 'init_temperature',
        'func': 'display_temperature'
    },
    {
        'key': 'TEXT',
        'init_func': 'init_text',
        'func': 'display_text'
    },
#    {
#        'key': 'RTCBAT',
#        'init_func': 'init_battery',
#        'func': 'display_battery'
#    }
]

# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

# Hardware objects
rtc_i2c = None
ldr_adc = None
bat_adc = None
temp_sensor = None
display = None

# LDR brightness filtering
filtered_brightness = None

# Battery monitoring
battery_samples = []  # Rolling buffer for battery voltage samples
battery_filtered_mv = None  # Last filtered battery voltage
battery_last_update = 0  # Last time battery reading was updated
battery_samples_avg_size = 15  # Number of samples for averaging

# Text cycling
text_index = 0
text_colors = None
last_text_change = 0

# Time display
blink_state = True
last_blink_time = 0

# ============================================================================
# INITIALIZATION FUNCTIONS
# ============================================================================

def init_time():
    """Initialize DS1307 RTC and related time components"""
    global rtc_i2c
    try:
        if sys.platform == "esp32":
            import machine
            # ESP32 I2C pins
            sda = machine.Pin(PIN_SDA)
            scl = machine.Pin(PIN_SCL)
            rtc_i2c = machine.I2C(0, scl=scl, sda=sda, freq=100000)

            # Check if DS1307 is present (address 0x68)
            devices = rtc_i2c.scan()
            if 0x68 in devices:
                check_and_init_rtc()
                return True
            else:
                return False
        else:
            return True
    except Exception as e:
        return False

def init_battery():
    """Initialize RTC battery monitoring ADC"""
    global bat_adc
    try:
        if sys.platform == "esp32":
            import machine
            bat_adc = machine.ADC(machine.Pin(PIN_BAT_RTC))
            bat_adc.atten(machine.ADC.ATTN_11DB)  # Full range 0-3.3V
            return True
        else:
            return False
    except Exception as e:
        return False

def init_ldr():
    """Initialize LDR (Light Dependent Resistor) for brightness control"""
    global ldr_adc
    try:
        if sys.platform == "esp32":
            import machine
            ldr_adc = machine.ADC(machine.Pin(PIN_LDR))
            ldr_adc.atten(machine.ADC.ATTN_11DB)  # Full range 0-3.3V
            return True
        else:
            return False
    except Exception as e:
        return False

def init_display():
    """Initialize the display hardware"""
    global display
    try:
        display = Display()
        # Add digits
        for i in range(DIGIT_COUNT):
            digit = Digit(i)
            display.extend(digit)

        # Set black background
        display.set_bg((0x00, 0x00, 0x00))
        return True
    except Exception as e:
        return False

def init_text():
    """Initialize text display - reset global variables used in display_text()"""
    global text_index, text_colors, last_text_change
    text_index = 0
    text_colors = None
    last_text_change = 0
    return True

def init_temperature():
    """Initialize temperature sensor (DS18B20 on GPIO10 for ESP32)"""
    global temp_sensor
    try:
        if sys.platform == "esp32":
            import machine
            import onewire
            import ds18x20

            # Initialize OneWire on GPIO10
            ow_pin = machine.Pin(PIN_TEMP)
            ow = onewire.OneWire(ow_pin)
            temp_sensor = ds18x20.DS18X20(ow)

            # Test if DS18B20 is connected
            devices = temp_sensor.scan()
            if len(devices) > 0:
                return True
            else:
                temp_sensor = None
                return False
        else:
            # For other platforms, there's no temperature reading
            return False
    except Exception as e:
        temp_sensor = None
        return False

def init():
    """Main initialization function - calls all init functions"""
    # Initialize display first
    if not init_display():
        return False

    # Initialize LDR for brightness control
    init_ldr()

    init_battery()

    # Initialize components from DISPLAY_ITEMS
    for item in DISPLAY_ITEMS:
        if item['init_func']:
            try:
                init_func = globals()[item['init_func']]
                success = init_func()
            except Exception as e:
                pass

    return True

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_time_ms():
    """Get current time in milliseconds for precise timing"""
    return time.time_ns() // 1000000  # Convert nanoseconds to milliseconds

def bcd_to_decimal(bcd):
    """Convert BCD (Binary Coded Decimal) to normal decimal"""
    return ((bcd >> 4) * 10) + (bcd & 0x0F)

def decimal_to_bcd(decimal):
    """Convert normal decimal to BCD (Binary Coded Decimal)"""
    return ((decimal // 10) << 4) | (decimal % 10)

def read_ldr_brightness():
    """Read LDR value and convert to brightness (0-31) with low-pass filter"""
    global filtered_brightness
    try:
        if ldr_adc is None:
            return 8  # Default brightness

        # ESP32: 12-bit ADC (0-4095)
        raw_value = ldr_adc.read()
        # Convert to 0-3.3V range
        voltage = raw_value * 3.3 / 4095

        # Map voltage to brightness (0-31)
        min_brightness = 1   # Minimum brightness in dark
        max_brightness = 16  # Maximum brightness in bright light

        # Voltage range: 2.5V (dark) to 3.3V (sunlight)
        voltage = max(2.5, min(3.3, voltage))
        normalized_voltage = (voltage - 2.5) / 0.8
        brightness = int(min_brightness + normalized_voltage * (max_brightness - min_brightness))
        brightness = max(min_brightness, min(max_brightness, brightness))

        # Low-pass filter: exponential moving average (smoothing factor 0.1)
        if filtered_brightness is None:
            filtered_brightness = brightness  # Initialize on first call
        alpha = 0.1  # Smoothing factor (0.0 = no change, 1.0 = no filtering)
        filtered_brightness = (alpha * brightness) + ((1 - alpha) * filtered_brightness)

        return int(filtered_brightness)

    except Exception as e:
        return 8  # Default brightness on error

def check_and_init_rtc():
    """Check if RTC needs initialization and set system time if needed"""
    try:
        if rtc_i2c is None:
            return False

        # Read seconds register to check clock halt bit
        data = rtc_i2c.readfrom_mem(0x68, 0x00, 1)
        seconds_reg = data[0]

        set_time = False

        # Check if clock halt bit (bit 7) is set
        if (seconds_reg & 0x80) != 0:
            set_time = True

        # Check if a file "set_time.txt" exists to force time set
        try:
            with open("set_time.txt", "r") as f:
                line = f.readline().strip()
                if len(line) == 8 and line[2] == ':' and line[5] == ':':
                    try:
                        hours, minutes, seconds = map(int, line.split(":"))
                        if 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59:
                            os.remove("set_time.txt")
                            return set_ds1307_time(hours, minutes, seconds)
                    except ValueError:
                        pass
            os.remove("set_time.txt")
            set_time = True
        except OSError:
            pass

        if set_time:
            hours, minutes, seconds = get_system_time()
            return set_ds1307_time(hours, minutes, seconds)

    except Exception as e:
        return False

def set_ds1307_time(hours, minutes, seconds):
    """Set time on DS1307 RTC"""
    try:
        if rtc_i2c is None:
            return False

        # Convert to BCD format
        sec_bcd = decimal_to_bcd(seconds) & 0x7F  # Clear clock halt bit
        min_bcd = decimal_to_bcd(minutes)
        hour_bcd = decimal_to_bcd(hours) & 0x3F   # 24-hour format

        # Write seconds, minutes, hours
        data = bytes([sec_bcd, min_bcd, hour_bcd])
        rtc_i2c.writeto_mem(0x68, 0x00, data)

        return True

    except Exception as e:
        return False

def read_ds1307_time():
    """Read time from DS1307 RTC"""
    try:
        if rtc_i2c is None:
            return None

        # Read 7 bytes from DS1307 starting at address 0x00
        data = rtc_i2c.readfrom_mem(0x68, 0x00, 7)

        # DS1307 format: [seconds, minutes, hours, weekday, day, month, year]
        seconds = bcd_to_decimal(data[0] & 0x7F)  # Mask out clock halt bit
        minutes = bcd_to_decimal(data[1])
        hours = bcd_to_decimal(data[2] & 0x3F)    # Mask out 12/24 hour bit

        return (hours, minutes, seconds)

    except Exception as e:
        return None

def get_system_time():
    """Fallback to system time"""
    t = time.localtime()
    return (t[3], t[4], t[5])  # hours, minutes, seconds

def read_temperature():
    """Read temperature in Celsius from DS18B20 or ESP32 MCU sensor"""
    global temp_sensor
    try:
        if sys.platform == "esp32":
            # ESP32 - read DS18B20 temperature sensor on GPIO10
            try:
                if temp_sensor is not None:
                    # Scan for DS18B20 devices
                    devices = temp_sensor.scan()
                    if len(devices) == 0:
                        return None

                    # Start temperature conversion
                    temp_sensor.convert_temp()

                    # Wait for conversion (DS18B20 needs ~750ms)
                    time.sleep(0.8)

                    # Read temperature from first device
                    temperature = temp_sensor.read_temp(devices[0])
                    return temperature
                else:
                    # Fallback to MCU temperature if DS18B20 not available
                    try:
                        import esp32
                        temperature = esp32.mcu_temperature()
                        return temperature
                    except AttributeError:
                        return None
            except (ImportError, AttributeError, OSError):
                return None
        else:
            return None

    except Exception as e:
        return None

def temperature_to_color(temp_c):
    """Convert temperature to color gradient: Blue (cold) -> Green -> Yellow -> Red (hot)"""
    if temp_c < 0:
        return (0x00, 0x00, 0xFF)  # Deep blue for freezing
    elif temp_c < 10:
        # Blue to cyan (0-10°C)
        t = temp_c / 10.0
        return (0x00, int(0xFF * t), 0xFF)
    elif temp_c < 20:
        # Cyan to green (10-20°C)
        t = (temp_c - 10) / 10.0
        return (0x00, 0xFF, int(0xFF * (1 - t)))
    elif temp_c < 30:
        # Green to yellow (20-30°C)
        t = (temp_c - 20) / 10.0
        return (int(0xFF * t), 0xFF, 0x00)
    elif temp_c < 40:
        # Yellow to red (30-40°C)
        t = (temp_c - 30) / 10.0
        return (0xFF, int(0xFF * (1 - t)), 0x00)
    else:
        # Hot red for >40°C
        return (0xFF, 0x00, 0x00)

def read_battery_voltage():
    """Read RTC battery voltage in millivolts with 5-sample averaging filter"""
    global battery_samples, battery_filtered_mv, battery_last_update

    try:
        if bat_adc is None:
            return battery_filtered_mv  # Return last known value if ADC not available

        current_time = get_time_ms()

        # Update samples every 100ms to get 5 samples over 0.5 seconds
        if current_time - battery_last_update >= 100:  # 100ms between samples
            # Read ADC value (ESP32: 12-bit ADC, 0-4095)
            raw_value = bat_adc.read()
            # Convert to voltage (0-3.3V range)
            va3_voltage = raw_value * 3.3 / 4095

            # Convert to millivolts
            vbat_mv = int(va3_voltage * 1000)

            # Add to rolling buffer (keep only last 5 samples)
            battery_samples.append(vbat_mv)
            if len(battery_samples) > battery_samples_avg_size:
                battery_samples.pop(0)  # Remove oldest sample

            # Calculate average if we have samples
            if len(battery_samples) > 0:
                battery_filtered_mv = sum(battery_samples) // len(battery_samples)

            battery_last_update = current_time

        return battery_filtered_mv

    except Exception as e:
        return battery_filtered_mv  # Return last known good value on error

def hue_to_rgb(hue):
    """Convert hue (0-360 degrees) to RGB color (0-255)"""
    # Normalize hue to 0-1 range
    h = (hue % 360) / 360.0

    # Simple HSV to RGB conversion with S=1, V=1
    i = int(h * 6)
    f = h * 6 - i

    if i == 0:
        return (255, int(f * 255), 0)
    elif i == 1:
        return (int((1 - f) * 255), 255, 0)
    elif i == 2:
        return (0, 255, int(f * 255))
    elif i == 3:
        return (0, int((1 - f) * 255), 255)
    elif i == 4:
        return (int(f * 255), 0, 255)
    else:
        return (255, 0, int((1 - f) * 255))

def generate_vibrant_gradient():
    """Generate vibrant gradient colors for text display"""
    import random

    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
        (255, 192, 203), # Pink
        (0, 255, 128),  # Spring green
    ]

    start_color = random.choice(colors)
    end_color = random.choice(colors)

    # Ensure different colors
    while start_color == end_color:
        end_color = random.choice(colors)

    return [start_color, end_color]

# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_time():
    """Display current time with rainbow colors if enabled"""
    global blink_state, last_blink_time

    try:
        # Get current time
        rtc_time = read_ds1307_time()
        if rtc_time:
            hours, minutes, seconds = rtc_time
        else:
            hours, minutes, seconds = get_system_time()

        # Handle blinking
        current_time = get_time_ms()
        if BLINK_COLON and (current_time - last_blink_time) > 500:  # 500ms blink interval
            blink_state = not blink_state
            last_blink_time = current_time

        # Format time string
        time_string = format_time_display(hours, minutes, seconds)

        # Update display
        display.set_text(time_string)

        # Apply rainbow colors if enabled
        if RAINBOW_NUMBERS:
            apply_rainbow_colors(hours, minutes, seconds)
        else:
            # Use solid cyan color
            display.set_fg((0x00, 0xFF, 0xFF))

        return time_string

    except Exception as e:
        return "TIME_ERR"

def display_text():
    """Display cycling text with vibrant gradient"""
    global text_index, text_colors, last_text_change

    try:
        if len(CYCLE_TEXT) > 0:
            # Handle text cycling within this function
            current_time = get_time_ms()

            # Initialize on first call
            if last_text_change == 0:
                last_text_change = current_time
                text_index = 0
                text_colors = generate_vibrant_gradient()

            # Advance text every CYCLE_TIME/len(CYCLE_TEXT) milliseconds
            text_cycle_interval = CYCLE_TIME // len(CYCLE_TEXT)  # Integer division for ms
            # Note: 3141ms / 9 items = 349ms per item, total = 349*9 = 3141ms

            # Calculate which text should be showing based on elapsed time since TEXT mode started
            # This ensures perfect synchronization with the main mode cycle
            time_diff = current_time - last_text_change

            # Calculate current position in the text cycle
            cycle_position = time_diff % CYCLE_TIME  # Position within the full TEXT mode cycle
            calculated_index = cycle_position // text_cycle_interval

            # Ensure we don't exceed array bounds
            if calculated_index >= len(CYCLE_TEXT):
                calculated_index = len(CYCLE_TEXT) - 1

            # Update index if it changed
            if calculated_index != text_index:
                text_index = calculated_index
                text_colors = generate_vibrant_gradient()

            current_text = CYCLE_TEXT[text_index]

            display.set_bg((0x00, 0x00, 0x00))  # Black background
            display.set_text(current_text)

            # Apply horizontal gradient using the display's gradient API
            if text_colors:
                display.set_gradient_fg('x', text_colors)  # 'x' for horizontal gradient
            else:
                display.set_fg((0xFF, 0x00, 0xFF))  # Fallback magenta

            return current_text
        else:
            display.set_fg((0xFF, 0x00, 0xFF))  # Magenta
            display.set_bg((0x00, 0x00, 0x00))
            display.set_text("EMPTY")
            return "EMPTY"
    except Exception as e:
        return "TEXT_ERR"

def display_temperature():
    """Display temperature with color coding"""
    temp_c = read_temperature()

    if temp_c is not None:
        # Convert to Fahrenheit if needed
        if USE_FAHRENHEIT:
            temp_f = (temp_c * 9.0 / 5.0) + 32.0
            temp_text = f"{temp_f:.1f}°F"
        else:
            temp_text = f"{temp_c:.1f}°C"

        # Set color based on temperature (always use Celsius for color calculation)
        temp_color = temperature_to_color(temp_c)
        display.set_fg(temp_color)
        display.set_bg((0x00, 0x00, 0x00))  # Black background

        # Display temperature
        display.set_text(temp_text)
        return temp_text
    else:
        # No temperature available
        display.set_fg((0xFF, 0xFF, 0xFF))  # White
        display.set_bg((0x00, 0x00, 0x00))
        display.set_text("NO TMP")
        return "NO TMP"

def display_battery():
    """Display RTC battery voltage"""

    vbat_mv = read_battery_voltage()

    if vbat_mv is not None:
        # Format voltage (e.g., "3250mV")
        bat_text = f"{vbat_mv}mV"

        # Color coding based on battery voltage
        if vbat_mv >= 2800:  # Good battery (>2.8V)
            bat_color = (0x00, 0xFF, 0x00)  # Green
        elif vbat_mv >= 2500:  # Warning (2.5-2.8V)
            bat_color = (0xFF, 0xFF, 0x00)  # Yellow
        elif vbat_mv >= 2400:  # Low (2.4-2.5V)
            bat_color = (0xFF, 0x80, 0x00)  # Orange
        else:  # Critical (<2.4V)
            bat_color = (0xFF, 0x00, 0x00)  # Red

        display.set_fg(bat_color)
        display.set_bg((0x00, 0x00, 0x00))  # Black background
        display.set_text(bat_text)

        return bat_text
    else:
        # No battery reading available
        display.set_fg((0x80, 0x80, 0x80))  # Gray
        display.set_bg((0x00, 0x00, 0x00))
        display.set_text("NO BAT")

        return "NO BAT"

def format_time_display(hours, minutes, seconds):
    """Format time for display based on configuration"""
    # Convert to 12h format if needed
    display_hours = hours
    am_pm = ""

    if not FORMAT_24H:
        if hours == 0:
            display_hours = 12
            am_pm = "A"  # AM
        elif hours < 12:
            display_hours = hours
            am_pm = "A"  # AM
        elif hours == 12:
            display_hours = 12
            am_pm = "P"  # PM
        else:
            display_hours = hours - 12
            am_pm = "P"  # PM

    if DIGIT_COUNT == 4:
        # 4 digits: HH:MM
        if FORMAT_24H:
            return f"{display_hours:02d}{minutes:02d}"
        else:
            # 12h format: H:MM + AM/PM indicator
            return f"{display_hours:2d}{minutes:02d}{am_pm}"

    elif DIGIT_COUNT == 6:
        if USE_SECONDS:
            # 6 digits with seconds: HH:MM:SS
            if FORMAT_24H:
                return f"{display_hours:02d}{minutes:02d}{seconds:02d}"
            else:
                # 12h format: HH:MM + AM/PM (no seconds in 12h mode for 6 digits)
                return f"{display_hours:2d}{minutes:02d} {am_pm}M"
        else:
            # 6 digits without seconds: "HH:MM " format
            if FORMAT_24H:
                return f"{display_hours:02d}{minutes:02d}  "
            else:
                return f"{display_hours:2d}{minutes:02d}{am_pm}M"

    return "ERROR"

def apply_rainbow_colors(hours, minutes, seconds):
    """Apply rainbow colors to time digits based on time values"""
    # Calculate hues based on time values
    if FORMAT_24H:
        hour_hue = (hours / 24.0) * 360  # 24-hour cycle
    else:
        # Convert to 12-hour for hue calculation
        display_hour = hours % 12
        if display_hour == 0:
            display_hour = 12
        hour_hue = (display_hour / 12.0) * 360  # 12-hour cycle

    minute_hue = (minutes / 60.0) * 360  # 60-minute cycle
    second_hue = (seconds / 60.0) * 360  # 60-second cycle

    # Convert hues to RGB colors
    hour_color = hue_to_rgb(hour_hue)
    minute_color = hue_to_rgb(minute_hue)
    second_color = hue_to_rgb(second_hue)

    if DIGIT_COUNT == 4:
        # 4 digits: HHMM (reversed indexing: digit 0 is rightmost)
        if FORMAT_24H:
            # HHMM format: digits [3][2][1][0] = H H M M
            display.set_digit_fg(3, hour_color)   # Hour tens (leftmost)
            display.set_digit_fg(2, hour_color)   # Hour ones
            display.set_digit_fg(1, minute_color) # Minute tens
            display.set_digit_fg(0, minute_color) # Minute ones (rightmost)
        else:
            # H:MMA format (3 actual time digits + AM/PM)
            if hours <= 9 or (not FORMAT_24H and hours % 12 <= 9):
                # Single digit hour: digits [3][2][1][0] = H M M A
                display.set_digit_fg(3, hour_color)   # Hour (leftmost)
                display.set_digit_fg(2, minute_color) # Minute tens
                display.set_digit_fg(1, minute_color) # Minute ones
                display.set_digit_fg(0, (0x00, 0xFF, 0xFF))  # AM/PM (rightmost)
            else:
                # Double digit hour: digits [3][2][1][0] = H H M M
                display.set_digit_fg(3, hour_color)   # Hour tens (leftmost)
                display.set_digit_fg(2, hour_color)   # Hour ones
                display.set_digit_fg(1, minute_color) # Minute tens
                display.set_digit_fg(0, minute_color) # Minute ones (rightmost)

    elif DIGIT_COUNT == 6:
        if USE_SECONDS and FORMAT_24H:
            # HHMMSS format: digits [5][4][3][2][1][0] = H H M M S S
            display.set_digit_fg(5, hour_color)   # Hour tens (leftmost)
            display.set_digit_fg(4, hour_color)   # Hour ones
            display.set_digit_fg(3, minute_color) # Minute tens
            display.set_digit_fg(2, minute_color) # Minute ones
            display.set_digit_fg(1, second_color) # Second tens
            display.set_digit_fg(0, second_color) # Second ones (rightmost)
        else:
            # Other 6-digit formats (HH:MM AM, etc.)
            display.set_digit_fg(5, hour_color)   # Hour tens/space (leftmost)
            display.set_digit_fg(4, hour_color)   # Hour ones
            display.set_digit_fg(3, minute_color) # Minute tens or ':'
            display.set_digit_fg(2, minute_color) # Minute ones
            display.set_digit_fg(1, (0x00, 0xFF, 0xFF))  # Separator/AM
            display.set_digit_fg(0, (0x00, 0xFF, 0xFF))  # Dot/PM (rightmost)

# ============================================================================
# MAIN LOOP FUNCTION
# ============================================================================

def func_loop():
    """Main loop function that cycles through DISPLAY_ITEMS"""
    current_item_index = 0
    last_mode_change = get_time_ms()
    brightness = 8  # Initialize brightness tracking

    try:
        loop_counter = 0
        while True:
            loop_counter += 1

            # Special case: display battery every 1000 loops for 100 loops
#            if loop_counter % 1000 < 100:
#                result = display_battery()
#                # Render and display result
#                if result is not None:
#                    display.render()
#                    print(f"[RTCBAT] {result}")
#                continue

            current_time = get_time_ms()

            # Update brightness periodically based on LDR
            if AUTO_BRIGHTNESS:
                new_brightness = read_ldr_brightness()
                if new_brightness != brightness:
                    brightness = new_brightness
                    display.set_brightness(brightness)

            # Check if it's time to cycle to next mode (CYCLE_TIME is in milliseconds)
            if (current_time - last_mode_change) >= CYCLE_TIME:
                current_item_index = (current_item_index + 1) % len(DISPLAY_ITEMS)
                last_mode_change = current_time
                # Re-initialize the new mode
                init_func_name = DISPLAY_ITEMS[current_item_index]['init_func']
                if init_func_name:
                    try:
                        init_func = globals()[init_func_name]
                        init_func()
                    except Exception as e:
                        pass

            # Get current display item
            current_item = DISPLAY_ITEMS[current_item_index]

            # Call the display function for current item
            try:
                func = globals()[current_item['func']]
                result = func()

                # Render and display result
                if result is not None:
                    display.render()
                    print(f"[{current_item['key']}] {result}")

            except Exception as e:
                display.set_fg((0xFF, 0x00, 0x00))  # Red for error
                display.set_text("ERROR")
                display.render()

            # Loop delay (convert milliseconds to seconds for time.sleep)
            time.sleep(LOOP_DELAY_MS / 1000.0)

    except KeyboardInterrupt:
        display.set_fg((0x00, 0x00, 0x00))
        display.set_bg((0x00, 0x00, 0x00))
        display.render()

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main entry point"""
    # Initialize all components
    if not init():
        return

    # Start the main loop
    func_loop()

if __name__ == "__main__":
    main()

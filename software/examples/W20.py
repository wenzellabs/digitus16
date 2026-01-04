#!/usr/bin/env python3
"""
W20 - Digital D20 Dice Roller
Simulates rolling a W20 dice on a 2-digit digitus16 display
Press button to roll with random duration
After 10 seconds of idle, displays time from RTC
"""

import sys
sys.path.insert(0, '..')
import time
import random
from display import Display
from digit import Digit

# Hardware Configuration
PIN_BUTTON = 7
PIN_SDA = 8  # GPIO8 - I2C SDA for RTC
PIN_SCL = 9  # GPIO9 - I2C SCL for RTC
PIN_TEMP = 10  # GPIO10 - DS18B20 temperature sensor

# Idle demo mode configuration
T_IDLE_DEMOMODE = 10  # seconds of idle before showing time

# W20 sequence - alternates between low and high numbers
W20_seq = [
    " 1",
    "20",
    " 2",
    "19",
    " 3",
    "18",
    " 4",
    "17",
    " 5",
    "16",
    " 6",
    "15",
    " 7",
    "14",
    " 8",
    "13",
    " 9",
    "12",
    "10",
    "11",
]

# Display colors
WHITE_FG = (0xFF, 0xFF, 0xFF)
BLACK_BG = (0x00, 0x00, 0x00)

# Rainbow colors for rolling animation
RAINBOW_COLORS = [
    (0x08, 0x00, 0x00),  # Red
    (0x08, 0x04, 0x00),  # Orange
    (0x08, 0x08, 0x00),  # Yellow
    (0x00, 0x08, 0x00),  # Green
    (0x00, 0x08, 0x08),  # Cyan
    (0x00, 0x00, 0x08),  # Blue
    (0x04, 0x00, 0x08),  # Purple
]

# Roll parameters
MAX_ROLL_TIME = 1.5  # seconds in phase 1
MIN_ROLL_COUNT = 10  # minimum loops in phase 2
MAX_ROLL_COUNT = 100 # maximum loops in phase 2

# Global RTC I2C object
rtc_i2c = None

# Global temperature sensor
temp_sensor = None

def bcd_to_decimal(bcd):
    """Convert BCD (Binary Coded Decimal) to normal decimal"""
    return ((bcd >> 4) * 10) + (bcd & 0x0F)

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

def setup_rtc():
    """Initialize I2C for DS1307 RTC"""
    global rtc_i2c
    try:
        import machine
        sda = machine.Pin(PIN_SDA)
        scl = machine.Pin(PIN_SCL)
        rtc_i2c = machine.I2C(0, scl=scl, sda=sda, freq=100000)
        print("RTC initialized")
        return True
    except Exception as e:
        print(f"RTC init failed: {e}")
        return False

def read_rtc_time():
    """Read time from DS1307 RTC, returns (hours, minutes, seconds) or None"""
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
        print(f"RTC read error: {e}")
        return None

def setup_temperature():
    """Initialize DS18B20 temperature sensor on GPIO10"""
    global temp_sensor
    try:
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
            print(f"Temperature sensor initialized ({len(devices)} device(s))")
            return True
        else:
            print("No DS18B20 found on GPIO10")
            temp_sensor = None
            return False
    except Exception as e:
        print(f"Temperature sensor init failed: {e}")
        temp_sensor = None
        return False

def read_temperature():
    """Read temperature in Celsius from DS18B20, returns float or None"""
    global temp_sensor
    try:
        if temp_sensor is None:
            print("Temperature: sensor not initialized")
            return None
        
        # Scan for DS18B20 devices
        devices = temp_sensor.scan()
        if len(devices) == 0:
            print("Temperature: no devices found on bus")
            return None
        
        # Start temperature conversion
        temp_sensor.convert_temp()
        
        # Wait for conversion (DS18B20 needs ~750ms)
        time.sleep(0.8)
        
        # Read temperature from first device
        temperature = temp_sensor.read_temp(devices[0])
        print(f"Temperature: {temperature:.1f}°C")
        return temperature
    except Exception as e:
        print(f"Temperature read error: {e}")
        return None

def start_temperature_conversion():
    """Start DS18B20 temperature conversion (non-blocking part)"""
    global temp_sensor
    try:
        if temp_sensor is None:
            return False
        
        # Scan for DS18B20 devices
        devices = temp_sensor.scan()
        if len(devices) == 0:
            return False
        
        # Start temperature conversion (non-blocking)
        temp_sensor.convert_temp()
        return True
    except Exception as e:
        return False

def finish_temperature_read():
    """Read temperature after conversion has completed"""
    global temp_sensor
    try:
        if temp_sensor is None:
            print("Temperature: sensor not initialized")
            return None
        
        # Scan for DS18B20 devices
        devices = temp_sensor.scan()
        if len(devices) == 0:
            print("Temperature: no devices found on bus")
            return None
        
        # Read temperature from first device (conversion should be done by now)
        temperature = temp_sensor.read_temp(devices[0])
        print(f"Temperature: {temperature:.1f}°C")
        return temperature
    except Exception as e:
        print(f"Temperature read error: {e}")
        return None

def setup_display():
    """Initialize 2-digit display"""
    display = Display()
    for i in range(2):
        digit = Digit(i)
        display.extend(digit)
    display.set_brightness(8)
    display.set_fg(WHITE_FG)
    display.set_bg(BLACK_BG)
    return display

def setup_button():
    """Setup button with pull-up (button connects to GND)"""
    try:
        import machine
        button = machine.Pin(PIN_BUTTON, machine.Pin.IN, machine.Pin.PULL_UP)
        return button
    except ImportError:
        # Fallback for non-MicroPython platforms
        print("Running without button support (not on MicroPython)")
        return None

def roll_dice(display, start_index=None):
    """
    Animate dice roll with random duration
    1) Pick random roll_time (0 to MAX_ROLL_TIME)
    2) Pick random roll_count (0 to MAX_ROLL_COUNT)
    3) Roll for roll_time seconds
    4) Then roll for roll_count more loops
    
    Args:
        display: The Display object
        start_index: Starting position in W20_seq (if None, pick random)
    
    Returns:
        Tuple of (final_result_text, final_index)
    """
    # Pick random roll parameters (don't re-seed, let random maintain state)
    roll_time = random.random() * MAX_ROLL_TIME
    roll_count = MIN_ROLL_COUNT + int(random.random() * MAX_ROLL_COUNT)
    
    print(f"  Roll time: {roll_time:.3f}s, Roll count: {roll_count}")
    
    # Start from random position if not specified, or continue from last position
    if start_index is None:
        seq_index = int(random.random() * len(W20_seq))
    else:
        seq_index = start_index
    
    # Rainbow color index for background animation
    color_index = 0
    
    # Phase 1: Roll for roll_time seconds
    display.set_fg(WHITE_FG)
    start_time = time.time()
    while time.time() - start_time < roll_time:
        display.set_text(W20_seq[seq_index])
        display.set_bg(RAINBOW_COLORS[color_index])
        display.render()
        seq_index = (seq_index + 1) % len(W20_seq)
        color_index = (color_index + 1) % len(RAINBOW_COLORS)
        time.sleep(0.001)  # 1ms sleep
    
    # Phase 2: Roll for roll_count more loops
    p2_delay = 0.002
    for _ in range(roll_count):
        display.set_text(W20_seq[seq_index])
        display.set_bg(RAINBOW_COLORS[color_index])
        display.render()
        seq_index = (seq_index + 1) % len(W20_seq)
        color_index = (color_index + 1) % len(RAINBOW_COLORS)
        time.sleep(p2_delay)
        p2_delay += 0.004
    
    # Final render with black background
    display.set_bg(BLACK_BG)
    display.render()
    
    # Return the final result and the index for next roll
    final_text = display.text
    final_index = seq_index
    
    return final_text, final_index

def rainbow_animation(display, duration=5.0):
    """
    Animate rainbow over all 32 LEDs for specified duration
    Colors advance across the display creating a moving rainbow effect
    
    Args:
        display: The Display object
        duration: Time in seconds to run the animation
    """
    start_time = time.time()
    color_offset = 0
    
    display.set_text("\xff\xff")  # Turn on all segments
    
    while time.time() - start_time < duration:
        # Create a rainbow gradient that shifts over time
        # Build color list that advances with color_offset
        colors = []
        for i in range(len(RAINBOW_COLORS)):
            idx = (i + color_offset) % len(RAINBOW_COLORS)
            colors.append(RAINBOW_COLORS[idx])
        
        # Set gradient on foreground (the lit segments)
        display.set_gradient_fg('x', colors)
        display.render()
        
        color_offset = (color_offset + 1) % len(RAINBOW_COLORS)
        time.sleep(0.1)  # 100ms per frame for smooth animation
    
    # Clear display after animation
    display.set_fg(WHITE_FG)
    display.set_bg(BLACK_BG)

def main():
    """Main application loop"""
    print("W20 Dice Roller")
    print("Press button on GPIO7 to roll the dice!")
    print("(Button should connect to GND with pull-up enabled)")
    print(f"Starting in demo mode, button exits to dice mode")
    print(f"Dice mode returns to demo after {T_IDLE_DEMOMODE} seconds of idle")
    
    # Setup
    display = setup_display()
    button = setup_button()
    setup_rtc()  # Initialize RTC
    setup_temperature()  # Initialize temperature sensor
    
    # Track last position to continue rolling from there
    last_index = None
    
    # Track last activity time for idle demo mode
    last_activity_time = time.time()
    
    # Start in demo mode
    in_demo_mode = True
    
    try:
        last_button_state = button.value()
        
        while True:
            # If in demo mode, run the demo loop
            if in_demo_mode:
                # Run one cycle of the demo
                button_pressed = show_time_demo_interruptible(display, button)
                
                if button_pressed:
                    # Button was pressed during demo - exit to dice mode and roll
                    in_demo_mode = False
                    
                    print("\n🎲 Rolling...")
                    random.seed(time.ticks_us())
                    result, last_index = roll_dice(display, last_index)
                    print(f"Result: {result.strip()}")
                    
                    # Reset idle timer on activity
                    last_activity_time = time.time()
                    
                    # Show result
                    display.set_text(result)
                    display.set_fg(WHITE_FG)
                    display.set_bg(BLACK_BG)
                    display.render()
                    
                    # Update button state
                    last_button_state = button.value()
                # else: demo completed normally, loop continues
            else:
                # In dice mode - check for button presses and idle timeout
                button_state = button.value()
                
                # Detect button press (transition from 1 to 0, since pull-up)
                if last_button_state == 1 and button_state == 0:
                    print("\n🎲 Rolling...")
                    random.seed(time.ticks_us())
                    result, last_index = roll_dice(display, last_index)
                    print(f"Result: {result.strip()}")
                    
                    # Reset idle timer on activity
                    last_activity_time = time.time()
                    
                    # Show result
                    display.set_text(result)
                    display.set_fg(WHITE_FG)
                    display.set_bg(BLACK_BG)
                    display.render()
                
                # Check for idle timeout to return to demo mode
                idle_time = time.time() - last_activity_time
                if idle_time >= T_IDLE_DEMOMODE:
                    print("\n⏰ Returning to demo mode...")
                    in_demo_mode = True
                
                last_button_state = button_state
                time.sleep(0.001)  # Small delay to prevent busy-waiting
                
    except KeyboardInterrupt:
        print("\n\nStopping dice roller...")
        display.set_fg(BLACK_BG)
        display.set_bg(BLACK_BG)
        display.render()
        print("Goodbye!")

def show_time_demo_interruptible(display, button):
    """
    Show complete demo sequence:
    1. Time (HH/MM/SS with values)
    2. Rainbow animation
    3. Temperature (°C with value)
    4. Rainbow animation
    
    Returns True if button was pressed (interrupted), False if completed normally
    """
    # Helper to check button during sleep
    def interruptible_sleep(duration):
        start = time.time()
        while time.time() - start < duration:
            if button.value() == 0:  # Button pressed
                return False  # Signal to exit
            time.sleep(0.01)
        return True  # Continue
    
    # === TIME DISPLAY ===
    
    # Read time from RTC
    time_tuple = read_rtc_time()
    if time_tuple is None:
        # Fallback to system time
        t = time.localtime()
        hours, minutes, seconds = t[3], t[4], t[5]
        print(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d} (system)")
    else:
        hours, minutes, seconds = time_tuple
        print(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d} (RTC)")
    
    # Format values as 2-digit strings
    hh_val = f"{hours:02d}"
    mm_val = f"{minutes:02d}"
    ss_val = f"{seconds:02d}"
    
    # Calculate hue-based colors
    hh_hue = (hours * 360) // 24
    mm_hue = (minutes * 360) // 60
    ss_hue = (seconds * 360) // 60
    
    hh_color = hue_to_rgb(hh_hue)
    mm_color = hue_to_rgb(mm_hue)
    ss_color = hue_to_rgb(ss_hue)
    
    display.set_bg(BLACK_BG)
    
    # "HH" with rainbow gradient
    display.set_text("HH")
    display.set_gradient_fg('x', RAINBOW_COLORS)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # Actual hours with hue-based color
    display.set_text(hh_val)
    display.set_fg(hh_color)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # "MM" with rainbow gradient
    display.set_text("MM")
    display.set_gradient_fg('x', RAINBOW_COLORS)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # Actual minutes with hue-based color
    display.set_text(mm_val)
    display.set_fg(mm_color)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # "SS" with rainbow gradient
    display.set_text("SS")
    display.set_gradient_fg('x', RAINBOW_COLORS)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # Actual seconds with hue-based color
    display.set_text(ss_val)
    display.set_fg(ss_color)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # === RAINBOW ANIMATION ===
    if rainbow_animation_interruptible(display, button, duration=5.0):
        return True  # Button pressed during animation
    
    # === TEMPERATURE DISPLAY ===
    
    # Start temperature conversion in background (takes ~800ms)
    start_temperature_conversion()
    
    # While conversion is happening, show "°C" label
    # "°C" with rainbow gradient
    display.set_text("\xb0C")  # °C
    display.set_gradient_fg('x', RAINBOW_COLORS)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # By now, temperature conversion should be complete
    # Read the temperature result
    temp_c = finish_temperature_read()
    
    if temp_c is not None:
        # Format temperature as 2-digit integer
        temp_val = f"{int(temp_c):2d}"
        
        # Calculate hue based on temperature (similar to blonkenclick color mapping)
        # Blue (cold) to red (hot): 0°C = 240° hue, 30°C = 0° hue
        if temp_c < 0:
            temp_hue = 240
        elif temp_c > 30:
            temp_hue = 0
        else:
            # Linear mapping: 0°C -> 240°, 30°C -> 0°
            temp_hue = int(240 - (temp_c / 30.0) * 240)
        
        temp_color = hue_to_rgb(temp_hue)
    else:
        # Sensor failed - show error
        temp_val = "ER"
        temp_color = (0xFF, 0x00, 0x00)  # Red for error
    
    # Display temperature value for full 1 second
    display.set_text(temp_val)
    display.set_fg(temp_color)
    display.render()
    if not interruptible_sleep(1.0):
        return True  # Button pressed
    
    # === FINAL RAINBOW ANIMATION ===
    if rainbow_animation_interruptible(display, button, duration=5.0):
        return True  # Button pressed during animation
    
    # Completed full cycle without interruption
    return False

def rainbow_animation_interruptible(display, button, duration=5.0):
    """
    Rainbow animation that can be interrupted by button press
    Returns True if button was pressed, False if completed normally
    """
    start_time = time.time()
    color_offset = 0
    
    display.set_text("\xff\xff")  # Turn on all segments
    
    while time.time() - start_time < duration:
        # Check for button press
        if button.value() == 0:
            return True  # Button pressed
        
        # Create a rainbow gradient that shifts over time
        colors = []
        for i in range(len(RAINBOW_COLORS)):
            idx = (i + color_offset) % len(RAINBOW_COLORS)
            colors.append(RAINBOW_COLORS[idx])
        
        display.set_gradient_fg('x', colors)
        display.render()
        
        color_offset = (color_offset + 1) % len(RAINBOW_COLORS)
        time.sleep(0.1)
    
    display.set_fg(WHITE_FG)
    display.set_bg(BLACK_BG)
    return False  # Completed normally

if __name__ == "__main__":
    main()
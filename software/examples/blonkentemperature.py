#!/usr/bin/env python3
"""
Blonken Temperature - Simple DS18B20 Temperature Display
Displays temperature from DS18B20 sensor on GPIO10
"""

import sys
import time
sys.path.insert(0, '..')
from display import Display
from digit import Digit

# Configuration
DIGIT_COUNT = 6
DS18B20_PIN = 10  # GPIO pin for DS18B20 sensor
UPDATE_INTERVAL = 2.0  # Update temperature every 2 seconds

def init_ds18b20():
    """Initialize DS18B20 temperature sensor on GPIO10"""
    try:
        if sys.platform == "rp2" or sys.platform == "esp32":
            import machine
            import onewire
            import ds18x20

            # Initialize OneWire on GPIO10
            ow_pin = machine.Pin(DS18B20_PIN)
            ow = onewire.OneWire(ow_pin)
            ds = ds18x20.DS18X20(ow)

            # Scan for DS18B20 devices
            devices = ds.scan()
            if len(devices) == 0:
                print(f"No DS18B20 devices found on GPIO{DS18B20_PIN}")
                return None, None

            print(f"Found {len(devices)} DS18B20 device(s) on GPIO{DS18B20_PIN}")
            for i, device in enumerate(devices):
                print(f"  Device {i}: {device.hex()}")

            return ds, devices[0]  # Return first device

        elif sys.platform.startswith("linux"):
            # Linux: simulate DS18B20 for testing
            print(f"DS18B20 simulated on GPIO{DS18B20_PIN} (Linux)")
            return "simulated", None

    except ImportError as e:
        print(f"DS18B20 library import error: {e}")
        print("Make sure onewire and ds18x20 modules are available")
        return None, None
    except Exception as e:
        print(f"DS18B20 initialization error: {e}")
        return None, None

def read_ds18b20_temperature(ds_sensor, device_addr):
    """Read temperature from DS18B20 sensor"""
    try:
        if ds_sensor is None:
            return None

        if ds_sensor == "simulated":
            # Linux simulation: random temperature
            import random
            return 20.0 + random.uniform(-5, 10)  # 15-30°C range

        # Start temperature conversion
        ds_sensor.convert_temp()

        # Wait for conversion (DS18B20 needs ~750ms)
        time.sleep(0.8)

        # Read temperature
        temp_c = ds_sensor.read_temp(device_addr)
        return temp_c

    except Exception as e:
        print(f"DS18B20 read error: {e}")
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

def format_temperature(temp_c, celsius=True):
    """Format temperature for display"""
    if temp_c is None:
        return "SENSOR"

    if celsius:
        # Display in Celsius: "23.4°C"
        return f"{temp_c:.1f}°C"
    else:
        # Display in Fahrenheit: "74.1°F"
        temp_f = temp_c * 9.0 / 5.0 + 32
        return f"{temp_f:.1f}°F"

def main():
    print("Blonken Temperature Display - DS18B20 Sensor")
    print(f"Sensor on GPIO{DS18B20_PIN}, update every {UPDATE_INTERVAL}s")

    # Create display
    display = Display()

    # Add digits
    for i in range(DIGIT_COUNT):
        digit = Digit(i)
        display.extend(digit)

    # Initialize DS18B20 sensor
    ds_sensor, device_addr = init_ds18b20()
    if ds_sensor is None:
        print("Failed to initialize DS18B20 sensor")
        return

    # Display colors
    error_color = (0xFF, 0x00, 0x00)  # Red
    bg_color = (0x00, 0x00, 0x00)    # Black

    display.set_bg(bg_color)
    last_update = 0

    try:
        while True:
            current_time = time.time()

            # Update temperature reading
            if (current_time - last_update) >= UPDATE_INTERVAL:
                temp_c = read_ds18b20_temperature(ds_sensor, device_addr)
                last_update = current_time

                if temp_c is not None:
                    # Format and display temperature
                    temp_text = format_temperature(temp_c, celsius=True)
                    temp_color = temperature_to_color(temp_c)
                    display.set_fg(temp_color)
                    display.set_text(temp_text)

                    print(f"Temperature: {temp_c:.2f}°C -> '{temp_text}' RGB{temp_color}")
                else:
                    # Sensor error
                    display.set_fg(error_color)
                    display.set_text("ERROR")
                    print("Sensor read error")

                display.render()

            # Small delay
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping temperature display...")
        display.set_fg((0x00, 0x00, 0x00))
        display.set_bg((0x00, 0x00, 0x00))
        display.render()

if __name__ == "__main__":
    main()

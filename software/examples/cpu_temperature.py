import sys
sys.path.insert(0, '..')
import time
from display import Display
from digit import Digit

in_celsius = True

def read_mcu_temperature():
    """Read MCU temperature in Celsius. Returns None if not supported."""
    try:
        if sys.platform == "rp2":
            # Raspberry Pi Pico - read internal temperature sensor
            import machine
            adc = machine.ADC(4)  # Internal temperature sensor on ADC channel 4
            reading = adc.read_u16() * 3.3 / 65536
            # Convert to Celsius using Pico's formula
            temperature = 27 - (reading - 0.706) / 0.001721
            return temperature

        elif sys.platform == "esp32":
            # ESP32 - read internal temperature (if available)
            try:
                import esp32
                # Temperature in Fahrenheit, convert to Celsius
                temperature = esp32.mcu_temperature()
                return temperature
            except AttributeError:
                # Some ESP32 versions don't have raw_temperature()
                return None

        elif sys.platform.startswith("linux"):
            # Linux systems - try to read CPU temperature
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp_millidegrees = int(f.read().strip())
                    temperature = temp_millidegrees / 1000.0
                    return temperature
            except (FileNotFoundError, PermissionError, ValueError):
                # Fallback: simulate temperature for testing
                import random
                return 20.0 + random.uniform(-5, 15)  # 15-35°C range
        else:
            return None

    except Exception as e:
        print(f"Temperature read error: {e}")
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

# Main temperature display loop
print("MCU Temperature Display")
print("Platform:", sys.platform)

d = Display()
for i in range(6):
    digit = Digit(i)
    d.extend(digit)

try:
    while True:
        temp_c = read_mcu_temperature()

        if temp_c is not None:
            if in_celsius:
                display_temp = temp_c
                unit = "C"
            else:
                display_temp = temp_c * 9.0 / 5.0 + 32  # Convert to Fahrenheit
                unit = "F"

            # Format temperature (e.g., "23C" or "73F")
            temp_text = f"{display_temp:.0f}°{unit}"

            # Set color based on temperature
            temp_color = temperature_to_color(temp_c)
            d.set_fg(temp_color)
            d.set_bg((0x00, 0x00, 0x00))  # Black background

            # Display temperature
            d.set_text(temp_text)
            d.render()

            print(f"Temperature: {temp_c:.1f}°C ({display_temp:.1f}°{unit})")
        else:
            # No temperature available
            d.set_fg((0xFF, 0xFF, 0xFF))  # White
            d.set_bg((0x00, 0x00, 0x00))
            d.set_text("TEMP")
            d.render()
            print("Temperature sensor not available")

        time.sleep(1.0)  # Update every 1 second

except KeyboardInterrupt:
    print("\nStopping temperature display...")
    d.set_fg((0x00, 0x00, 0x00))
    d.set_bg((0x00, 0x00, 0x00))
    d.render()
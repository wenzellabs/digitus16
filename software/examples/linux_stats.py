#!/usr/bin/env python3
"""
Linux System Stats Display
Cycles through various system metrics with color-coded values
"""

import sys
import time
import psutil
import os
sys.path.insert(0, '..')
from display import Display
from digit import Digit

# Configuration
DIGIT_COUNT = 6
CYCLE_TIME = 2.0  # Time in seconds to display each metric

# Metric definitions with their display colors
METRICS = [
    {
        'key': 'Memory',
        'color': (0xFF, 0x00, 0xFF),  # Magenta
        'func': 'get_memory_usage'
    },
    {
        'key': 'Disk',
        'color': (0x00, 0xFF, 0xFF),  # Cyan
        'func': 'get_disk_usage'
    },
    {
        'key': 'CPU',
        'color': (0xFF, 0xFF, 0x00),  # Yellow
        'func': 'get_cpu_usage'
    },
    {
        'key': 'Load',
        'color': (0xFF, 0x80, 0x00),  # Orange
        'func': 'get_load_average'
    },
    {
        'key': 'Temp',
        'color': (0xFF, 0x00, 0x00),  # Red
        'func': 'get_cpu_temperature'
    },
    {
        'key': 'Net RX',
        'color': (0x00, 0xFF, 0x00),  # Green
        'func': 'get_network_rx'
    },
    {
        'key': 'Net TX',
        'color': (0x80, 0xFF, 0x00),  # Light Green
        'func': 'get_network_tx'
    },
    {
        'key': 'UTC',
        'color': (0x80, 0xFF, 0x80),
        'func': 'get_utc_time'
    },
]

# Network tracking for delta calculations
last_net_stats = None
last_net_time = None

def percentage_to_color(percentage):
    """Convert percentage (0-100) to color gradient: Green (good) -> Red (bad)"""
    # Clamp percentage to 0-100 range
    pct = max(0, min(100, percentage))

    if pct <= 50:
        # Green to Yellow (0-50%)
        t = pct / 50.0
        return (int(0xFF * t), 0xFF, 0x00)
    else:
        # Yellow to Red (50-100%)
        t = (pct - 50) / 50.0
        return (0xFF, int(0xFF * (1 - t)), 0x00)

def value_to_color_scale(value, min_val, max_val, reverse=False):
    """Convert value to color scale. If reverse=True, higher values are better (green)"""
    # Normalize value to 0-100 percentage
    if max_val == min_val:
        pct = 0
    else:
        pct = ((value - min_val) / (max_val - min_val)) * 100

    if reverse:
        pct = 100 - pct  # Flip for reverse scaling

    return percentage_to_color(pct)

def get_memory_usage():
    """Get memory usage percentage"""
    try:
        mem = psutil.virtual_memory()
        percentage = mem.percent
        return f"{percentage:.0f}%", percentage_to_color(percentage)
    except Exception as e:
        return "ERR", (0xFF, 0xFF, 0xFF)

def get_disk_usage():
    """Get disk usage percentage for root filesystem"""
    try:
        disk = psutil.disk_usage('/')
        percentage = (disk.used / disk.total) * 100
        return f"{percentage:.0f}%", percentage_to_color(percentage)
    except Exception as e:
        return "ERR", (0xFF, 0xFF, 0xFF)

def get_cpu_usage():
    """Get CPU usage percentage"""
    try:
        # Get CPU usage over a short interval
        cpu_pct = psutil.cpu_percent(interval=0.1)
        return f"{cpu_pct:.0f}%", percentage_to_color(cpu_pct)
    except Exception as e:
        return "ERR", (0xFF, 0xFF, 0xFF)

def get_load_average():
    """Get 1-minute load average"""
    try:
        load1, load5, load15 = psutil.getloadavg()
        cpu_count = psutil.cpu_count()

        # Convert to percentage relative to CPU count
        load_pct = (load1 / cpu_count) * 100 if cpu_count > 0 else 0

        # Format based on value
        if load1 < 10:
            display_val = f"{load1:.1f}"
        else:
            display_val = f"{load1:.0f}"

        return display_val, percentage_to_color(load_pct)
    except Exception as e:
        return "ERR", (0xFF, 0xFF, 0xFF)

def get_cpu_temperature():
    """Get CPU temperature"""
    try:
        # Try to read from thermal zone
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_millidegrees = int(f.read().strip())
            temp_celsius = temp_millidegrees / 1000.0

        # Color scale: 30°C (green) to 80°C (red)
        color = value_to_color_scale(temp_celsius, 30, 80)
        return f"{temp_celsius:.0f}°C", color

    except Exception as e:
        # Fallback: try psutil sensors
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Get first available temperature sensor
                for entries in temps.items():
                    if entries:
                        temp = entries[0].current
                        color = value_to_color_scale(temp, 30, 80)
                        return f"{temp:.0f}°C", color
        except:
            pass
        return "N/A", (0x80, 0x80, 0x80)

def get_network_rx():
    """Get network receive rate in KB/s"""
    global last_net_stats, last_net_time
    try:
        current_stats = psutil.net_io_counters()
        current_time = time.time()

        if last_net_stats is not None and last_net_time is not None:
            time_delta = current_time - last_net_time
            if time_delta > 0:
                bytes_delta = current_stats.bytes_recv - last_net_stats.bytes_recv
                kbps = (bytes_delta / time_delta) / 1024  # KB/s

                # Color scale: 0 KB/s (green) to 1000 KB/s (red)
                color = value_to_color_scale(kbps, 0, 1000)

                # Format display
                if kbps < 10:
                    display_val = f"{kbps:.1f}KB"
                elif kbps < 1000:
                    display_val = f"{kbps:.0f}KB"
                else:
                    display_val = f"{kbps/1024:.1f}MB"

                return display_val, color

        # Update tracking variables
        last_net_stats = current_stats
        last_net_time = current_time
        return "0KB", (0x00, 0xFF, 0x00)

    except Exception as e:
        return "ERR", (0xFF, 0xFF, 0xFF)

def get_network_tx():
    """Get network transmit rate in KB/s"""
    try:
        current_stats = psutil.net_io_counters()
        current_time = time.time()

        if hasattr(get_network_tx, 'last_stats') and hasattr(get_network_tx, 'last_time'):
            time_delta = current_time - get_network_tx.last_time
            if time_delta > 0:
                bytes_delta = current_stats.bytes_sent - get_network_tx.last_stats.bytes_sent
                kbps = (bytes_delta / time_delta) / 1024  # KB/s

                # Color scale: 0 KB/s (green) to 1000 KB/s (red)
                color = value_to_color_scale(kbps, 0, 1000)

                # Format display
                if kbps < 10:
                    display_val = f"{kbps:.1f}KB"
                elif kbps < 1000:
                    display_val = f"{kbps:.0f}KB"
                else:
                    display_val = f"{kbps/1024:.1f}MB"

                # Update tracking
                get_network_tx.last_stats = current_stats
                get_network_tx.last_time = current_time

                return display_val, color

        # Initialize tracking
        get_network_tx.last_stats = current_stats
        get_network_tx.last_time = current_time
        return "0KB", (0x00, 0xFF, 0x00)

    except Exception as e:
        return "ERR", (0xFF, 0xFF, 0xFF)

def get_utc_time():
    """Get current UTC time in HH:MM:SS format"""
    try:
        import datetime
        utc_now = datetime.datetime.utcnow()
        time_str = utc_now.strftime("%H%M%S")

        # Color based on time of day (darker at night, brighter during day)
        hour = utc_now.hour
        if 6 <= hour < 18:  # Daytime (6 AM - 6 PM UTC)
            # Brighter colors during day
            color = (0xFF, 0xFF, 0x00)  # Yellow
        elif 18 <= hour < 22:  # Evening (6 PM - 10 PM UTC)
            # Orange for evening
            color = (0xFF, 0x80, 0x00)  # Orange
        else:  # Night time (10 PM - 6 AM UTC)
            # Darker colors at night
            color = (0x00, 0x80, 0xFF)  # Blue

        return time_str, color

    except Exception as e:
        return "ERR", (0xFF, 0xFF, 0xFF)

def main():
    print("Linux System Stats Display")
    print("Cycling through system metrics...")
    print("Press Ctrl+C to exit")

    # Create display
    display = Display()

    # Add digits
    for i in range(DIGIT_COUNT):
        digit = Digit(i)
        display.extend(digit)

    # Set black background
    display.set_bg((0x00, 0x00, 0x00))

    # Cycling variables
    current_metric_index = 0
    last_cycle_time = time.time()
    show_key = True  # Alternate between showing key and value
    last_toggle_time = time.time()

    try:
        while True:
            current_time = time.time()

            # Check if it's time to cycle to next metric
            if (current_time - last_cycle_time) >= CYCLE_TIME:
                current_metric_index = (current_metric_index + 1) % len(METRICS)
                last_cycle_time = current_time
                show_key = True  # Always show key first when switching metrics
                last_toggle_time = current_time

            # Toggle between key and value every 1 second
            elif (current_time - last_toggle_time) >= 1.0:
                show_key = not show_key
                last_toggle_time = current_time

            # Get current metric
            metric = METRICS[current_metric_index]

            if show_key:
                # Show metric key with its signature color
                display_text = metric['key']
                display.set_fg(metric['color'])
            else:
                # Show metric value with color-coded result
                try:
                    func = globals()[metric['func']]
                    value_text, value_color = func()
                    display_text = value_text
                    display.set_fg(value_color)
                except Exception as e:
                    display_text = "ERR"
                    display.set_fg((0xFF, 0xFF, 0xFF))
                    print(f"Error getting {metric['key']}: {e}")

            # Update display
            display.set_text(display_text)
            display.render()

            # Print current status
            print(f"\r[{metric['key']}] {'KEY' if show_key else 'VAL'}: {display_text}", end='', flush=True)

            # Short delay
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopping Linux stats display...")
        display.set_fg((0x00, 0x00, 0x00))
        display.set_bg((0x00, 0x00, 0x00))
        display.render()

if __name__ == "__main__":
    main()

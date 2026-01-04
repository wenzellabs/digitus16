#!/usr/bin/env python3
"""
W20 - Digital D20 Dice Roller
Simulates rolling a W20 dice on a 2-digit digitus16 display
Press button to roll with random duration
"""

import sys
sys.path.insert(0, '..')
import time
import random
from display import Display
from digit import Digit

# Hardware Configuration
PIN_BUTTON = 7

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

def main():
    """Main application loop"""
    print("W20 Dice Roller")
    print("Press button on GPIO7 to roll the dice!")
    print("(Button should connect to GND with pull-up enabled)")
    
    # Setup
    display = setup_display()
    button = setup_button()
    
    # Track last position to continue rolling from there
    last_index = None
    
    # Initial display - show waiting state
    display.set_text("--")
    display.render()
    
    try:
        last_button_state = button.value()
        
        while True:
            button_state = button.value()
            
            # Detect button press (transition from 1 to 0, since pull-up)
            if last_button_state == 1 and button_state == 0:
                print("\n🎲 Rolling...")
                random.seed(time.ticks_us())
                result, last_index = roll_dice(display, last_index)
                print(f"Result: {result.strip()}")
                
            last_button_state = button_state
            time.sleep(0.001)  # Small delay to prevent busy-waiting
                
    except KeyboardInterrupt:
        print("\n\nStopping dice roller...")
        display.set_fg(BLACK_BG)
        display.set_bg(BLACK_BG)
        display.render()
        print("Goodbye!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Seasons color cycling display - shows "Winter", "Spring", "Summer", "Fall"
with seasonal color gradients for foreground and background
"""

import sys
sys.path.insert(0, '..')
import time
from display import Display, Layer
from digit import Digit

# Winter colors - cool blues, whites, grays
WINTER_FG = [
    (0xF0, 0xF8, 0xFF),  # Alice blue (light)
    (0xB0, 0xC4, 0xDE),  # Light steel blue
    (0x87, 0xCE, 0xEB),  # Sky blue
    (0x46, 0x82, 0xB4),  # Steel blue
    (0x19, 0x19, 0x70)   # Midnight blue (dark)
]

WINTER_BG = [
    (0x01, 0x01, 0x05),  # Ultra dark blue
    (0x02, 0x02, 0x06),  # Deep navy
    (0x03, 0x03, 0x07),  # Very dark blue
    (0x04, 0x04, 0x08),  # Darker blue
    (0x05, 0x05, 0x09)   # Dark midnight blue
]

# Spring colors - fresh greens, light pastels
SPRING_FG = [
    (0x90, 0xEE, 0x90),  # Light green
    (0x98, 0xFB, 0x98),  # Pale green
    (0x32, 0xCD, 0x32),  # Lime green
    (0x22, 0x8B, 0x22),  # Forest green
    (0x00, 0x64, 0x00)   # Dark green
]

SPRING_BG = [
    (0x00, 0x04, 0x00),  # Ultra dark green
    (0x01, 0x05, 0x01),  # Deep forest green
    (0x02, 0x06, 0x02),  # Very dark green
    (0x03, 0x07, 0x03),  # Darker green
    (0x04, 0x08, 0x04)   # Deep emerald
]

# Summer colors - vibrant flower garden with yellows, reds, greens, blues
SUMMER_FG = [
    (0xFF, 0xFF, 0x00),  # Bright yellow (sunflower)
    (0xFF, 0x14, 0x93),  # Deep pink (rose)
    (0x32, 0xCD, 0x32),  # Lime green (grass)
    (0x00, 0x7F, 0xFF),  # Azure blue (sky/cornflower)
    (0xFF, 0x69, 0xB4)   # Hot pink (summer blooms)
]

SUMMER_BG = [
    (0x0A, 0x0A, 0x00),  # Ultra dark yellow
    (0x0A, 0x01, 0x05),  # Very dark pink
    (0x02, 0x08, 0x02),  # Ultra dark green
    (0x00, 0x04, 0x0A),  # Very dark blue
    (0x0A, 0x03, 0x06)   # Dark pink-purple
]

# Autumn colors - oranges, browns, deep reds
AUTUMN_FG = [
    (0xFF, 0x8C, 0x00),  # Dark orange
    (0xFF, 0x45, 0x00),  # Red orange
    (0xB2, 0x22, 0x22),  # Fire brick
    (0x8B, 0x45, 0x13),  # Saddle brown
    (0x65, 0x43, 0x21)   # Dark brown
]

AUTUMN_BG = [
    (0x05, 0x03, 0x01),  # Ultra dark brown
    (0x06, 0x02, 0x00),  # Deep maroon
    (0x07, 0x04, 0x03),  # Very dark chocolate
    (0x08, 0x05, 0x04),  # Deep brown
    (0x09, 0x06, 0x05)   # Dark amber
]

SEASONS = [
    ("Winter", WINTER_FG, WINTER_BG),
    ("Spring", SPRING_FG, SPRING_BG),
    ("Summer", SUMMER_FG, SUMMER_BG),
    ("Autumn", AUTUMN_FG, AUTUMN_BG)
]

def main():
    print("Seasons color cycling demo")

    # Create display with 6 digits for season names
    display = Display()

    # Add 6 digits for the longest season name
    for i in range(6):
        digit = Digit(i)
        display.extend(digit)

    display.set_brightness(8)

    print(f"Display has {display.digit_count} digits")

    # Cycle through seasons
    season_index = 0

    def interpolate_color(color1, color2, t):
        """Interpolate between two RGB colors. t=0 gives color1, t=1 gives color2"""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return (r, g, b)

    def interpolate_gradient(grad1, grad2, t):
        """Interpolate between two color gradients"""
        result = []
        min_len = min(len(grad1), len(grad2))
        for i in range(min_len):
            result.append(interpolate_color(grad1[i], grad2[i], t))
        return result

    try:
        while True:
            current_season = SEASONS[season_index]
            next_season = SEASONS[(season_index + 1) % len(SEASONS)]

            current_name, current_fg, current_bg = current_season
            next_name, next_fg, next_bg = next_season

            print(f"\nDisplaying: {current_name.strip()} -> {next_name.strip()}")

            # Animation settings
            fps = 10
            step_time = 1.0 / fps  # 100ms per frame at 10fps

            # Phase 1: Background breathing animation (3 seconds total)
            display.set_text(current_name)
            display.set_gradient_fg('y', current_fg)

            # Create black gradient (same length as current_bg)
            black_bg = [(0x00, 0x00, 0x00)] * len(current_bg)

            # Sub-phase 1a: BG morph to black (1 second)
            fade_steps = int(1.0 * fps)  # 10 steps for 1 second at 10fps
            for step in range(fade_steps + 1):
                t = step / fade_steps  # 0.0 to 1.0
                fade_bg = interpolate_gradient(current_bg, black_bg, t)
                display.set_gradient_bg('y', fade_bg)
                display.render()
                time.sleep(step_time)

            # Sub-phase 1b: BG stays black (1 second)
            display.set_gradient_bg('y', black_bg)
            display.render()
            time.sleep(1.0)

            # Sub-phase 1c: BG morph back from black (1 second)
            for step in range(fade_steps + 1):
                t = step / fade_steps  # 0.0 to 1.0
                fade_bg = interpolate_gradient(black_bg, current_bg, t)
                display.set_gradient_bg('y', fade_bg)
                display.render()
                time.sleep(step_time)

            # Phase 2: Morph colors over 4 seconds, change word at 2 seconds
            morph_duration = 4.0
            word_change_time = 2.0
            steps = int(morph_duration * fps)  # 40 steps for 4 seconds at 10fps

            for step in range(steps + 1):
                t = step / steps  # 0.0 to 1.0
                elapsed = step * step_time

                # Change word at 2 seconds (halfway through morph)
                if elapsed >= word_change_time and step > 0:
                    current_word = next_name
                else:
                    current_word = current_name

                # Interpolate colors
                morph_fg = interpolate_gradient(current_fg, next_fg, t)
                morph_bg = interpolate_gradient(current_bg, next_bg, t)

                # Apply morphed colors
                display.set_text(current_word)
                display.set_gradient_fg('y', morph_fg)
                display.set_gradient_bg('y', morph_bg)
                display.render()

                time.sleep(step_time)

            # Move to next season
            season_index = (season_index + 1) % len(SEASONS)

    except KeyboardInterrupt:
        print("\nStopping seasons demo...")
        # Turn off all LEDs
        #display.set_fg((0, 0, 0))
        #display.set_bg((0, 0, 0))
        #display.render()

if __name__ == "__main__":
    main()

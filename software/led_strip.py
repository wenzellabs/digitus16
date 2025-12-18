from led import LED

class LED_strip:
    def __init__(self, count:int=1):
        self._count = count
        self.LEDs = []
        for l in range(self._count):
            self.LEDs.append(LED())

    def led_count(self):
        return self._count

    def get_leds(self):
        return self.LEDs

    def set_fg(self, rgb):
        for l in self.LEDs:
            l.set_fg(rgb)

    def set_bg(self, rgb):
        for l in self.LEDs:
            l.set_bg(rgb)

    def turn_on(self):
        for l in self.LEDs:
            l.turn_on()

    def turn_off(self):
        for l in self.LEDs:
            l.turn_off()

    def get_color(self):
        return [rgb.get_color() for rgb in self.LEDs]
class LED:
    def __init__(self, x=0.0, y=0.0, on=True):
        self._fg_r = 20
        self._fg_g = 20
        self._fg_b = 20
        self._bg_r = 0
        self._bg_g = 0
        self._bg_b = 0
        self._on = on
        self._x = x
        self._y = y

    def set_fg(self, rgb):
        r, g, b = rgb
        self._fg_r = r
        self._fg_g = g
        self._fg_b = b

    def set_bg(self, rgb):
        r, g, b = rgb
        self._bg_r = r
        self._bg_g = g
        self._bg_b = b

    def turn_on(self):
        self._on = True

    def turn_off(self):
        self._on = False

    def is_on(self):
        return self._on

    def get_fg_color(self):
        return (self._fg_r, self._fg_g, self._fg_b)

    def get_bg_color(self):
        return (self._bg_r, self._bg_g, self._bg_b)

    def get_color(self):
        if self._on:
            return self.get_fg_color()
        else:
            return self.get_bg_color()

    def get_x(self):
        return self._x

    def set_x(self, x):
        self._x = x

    def get_y(self):
        return self._y

    def set_y(self, y):
        self._y = y

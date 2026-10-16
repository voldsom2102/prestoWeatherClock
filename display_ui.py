"""Layout and drawing for the digital clock + weather screen."""

import weather_icons
from timeutil import format_date, format_time

MARGIN = 12
# The bitmap font PicoGraphics draws with `display.text()` is an 8x8 grid,
# so a line rendered at a given scale is `scale * 8` pixels tall.
FONT_UNIT = 8


class ClockFace:
    def __init__(self, display, config):
        self.display = display
        self.config = config
        self.width, self.height = display.get_bounds()

        # A compact, roughly full-res-vs-low-res scale, tuned for both the
        # 240x240 default resolution and the optional 480x480 full_res mode.
        self.big_scale = 9 if self.width >= 400 else 5
        self.date_scale = 3 if self.width >= 400 else 2
        self.temp_scale = 6 if self.width >= 400 else 3
        self.small_scale = 2 if self.width >= 400 else 1

        self.bg = display.create_pen(8, 10, 20)
        self.fg = display.create_pen(235, 240, 250)
        self.dim = display.create_pen(120, 130, 150)
        self.accent = display.create_pen(90, 170, 255)
        self.warn = display.create_pen(230, 90, 70)

    def draw(self, now, weather, weather_error):
        d = self.display
        year, month, day, hour, minute, second, _, _ = now

        d.set_pen(self.bg)
        d.clear()

        y = MARGIN * 2
        y = self._draw_centered_text(
            format_time(hour, minute, second, self.config.USE_24_HOUR_CLOCK, self.config.SHOW_SECONDS),
            y,
            self.big_scale,
            self.fg,
        )

        y += MARGIN
        y = self._draw_centered_text(
            format_date(year, month, day),
            y,
            self.date_scale,
            self.dim,
        )

        y += MARGIN * 2
        self._draw_weather(y, weather, weather_error)

    def _draw_centered_text(self, text, y, scale, pen):
        d = self.display
        d.set_pen(pen)
        text_width = d.measure_text(text, scale)
        x = max((self.width - text_width) // 2, 0)
        d.text(text, x, y, self.width, scale)
        return y + (scale * FONT_UNIT)

    def _draw_weather(self, y, weather, weather_error):
        d = self.display

        if weather is None:
            message = "Weather unavailable" if weather_error else "Loading weather..."
            self._draw_centered_text(message, y, self.small_scale, self.warn if weather_error else self.dim)
            return

        icon_r = self.temp_scale * FONT_UNIT // 2
        icon_cx = self.width // 2 - (icon_r * 3)
        icon_cy = y + icon_r
        weather_icons.draw(d, weather.get("icon"), icon_cx, icon_cy, icon_r, self.fg, self.accent)

        units_symbol = "C" if self.config.UNITS == "metric" else "F"
        temp = weather.get("temp")
        temp_str = "--" if temp is None else "{:.0f}\u00b0{}".format(temp, units_symbol)

        d.set_pen(self.fg)
        temp_x = self.width // 2 - (icon_r // 2)
        d.text(temp_str, temp_x, y, self.width - temp_x, self.temp_scale)

        y += self.temp_scale * FONT_UNIT + MARGIN // 2
        description = weather.get("description") or ""
        # MicroPython's str has no .capitalize(), so do it by hand.
        if description:
            description = description[0].upper() + description[1:]
            y = self._draw_centered_text(description, y, self.small_scale, self.dim)

        if weather_error:
            y += MARGIN // 2
            self._draw_centered_text(
                "Showing last known reading",
                y,
                self.small_scale,
                self.warn,
            )

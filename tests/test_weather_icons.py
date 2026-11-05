import unittest

import weather_icons


class FakeDisplay:
    """Records drawing calls instead of touching real hardware."""

    def __init__(self):
        self.calls = []
        self.current_pen = None

    def set_pen(self, pen):
        self.current_pen = pen
        self.calls.append(("set_pen", pen))

    def circle(self, x, y, r):
        self.calls.append(("circle", x, y, r))

    def rectangle(self, x, y, w, h):
        self.calls.append(("rectangle", x, y, w, h))

    def line(self, x1, y1, x2, y2):
        self.calls.append(("line", x1, y1, x2, y2))

    def triangle(self, x1, y1, x2, y2, x3, y3):
        self.calls.append(("triangle", x1, y1, x2, y2, x3, y3))

    def create_pen(self, r, g, b):
        return (r, g, b)


class DrawIconTests(unittest.TestCase):
    def setUp(self):
        self.display = FakeDisplay()

    def _kinds_used(self):
        return {call[0] for call in self.display.calls}

    def test_clear_sky_draws_a_sun(self):
        weather_icons.draw(self.display, "01d", 50, 50, 10, fg=1, accent=2)
        self.assertIn("circle", self._kinds_used())
        self.assertIn("line", self._kinds_used())

    def test_broken_clouds_draws_cloud_only(self):
        weather_icons.draw(self.display, "04d", 50, 50, 10, fg=1, accent=2)
        self.assertIn("circle", self._kinds_used())
        self.assertIn("rectangle", self._kinds_used())

    def test_rain_draws_cloud_and_drops(self):
        weather_icons.draw(self.display, "10d", 50, 50, 10, fg=1, accent=2)
        kinds = self._kinds_used()
        self.assertIn("circle", kinds)
        self.assertIn("line", kinds)

    def test_thunderstorm_draws_bolt(self):
        weather_icons.draw(self.display, "11d", 50, 50, 10, fg=1, accent=2)
        self.assertIn("line", self._kinds_used())

    def test_mist_draws_only_rectangles(self):
        self.display = FakeDisplay()
        weather_icons.draw(self.display, "50d", 50, 50, 10, fg=1, accent=2)
        kinds = self._kinds_used()
        self.assertIn("rectangle", kinds)
        self.assertNotIn("circle", kinds)

    def test_unknown_icon_code_falls_back_to_cloud(self):
        weather_icons.draw(self.display, None, 50, 50, 10, fg=1, accent=2)
        self.assertIn("circle", self._kinds_used())

    def test_size_is_never_below_minimum(self):
        # A size of 0 (or a tiny icon area) shouldn't produce a zero-radius
        # icon that would be invisible.
        weather_icons.draw(self.display, "01d", 50, 50, 0, fg=1, accent=2)
        circle_calls = [c for c in self.display.calls if c[0] == "circle"]
        self.assertTrue(all(c[3] > 0 for c in circle_calls))


class FiveCIconTests(unittest.TestCase):
    def setUp(self):
        self.display = FakeDisplay()

    def _draw(self, code, bg=None):
        weather_icons.draw(self.display, code, 50, 50, 10, fg=1, accent=2, icon_set="5c", bg=bg)
        return {call[0] for call in self.display.calls}

    def _pens_used(self):
        return {call[1] for call in self.display.calls if call[0] == "set_pen"}

    def test_every_family_draws_something(self):
        for code in ("01d", "01n", "02d", "02n", "03d", "04n", "09d", "10d", "11d", "13d", "50d", None):
            self.display = FakeDisplay()
            self.assertTrue(self._draw(code), code)

    def test_uses_own_colours_not_fg_or_accent(self):
        self._draw("10d")
        self.assertNotIn(1, self._pens_used())
        self.assertNotIn(2, self._pens_used())

    def test_rain_draws_triangle_drops(self):
        self.assertIn("triangle", self._draw("10d"))

    def test_night_clear_cuts_crescent_with_background_pen(self):
        self._draw("01n", bg="BG")
        self.assertIn("BG", self._pens_used())

    def test_day_clear_does_not_use_background_pen(self):
        self._draw("01d", bg="BG")
        self.assertNotIn("BG", self._pens_used())

    def test_unknown_set_falls_back_to_classic(self):
        weather_icons.draw(self.display, "01d", 50, 50, 10, fg=1, accent=2, icon_set="nope")
        self.assertIn(("set_pen", 2), self.display.calls)


if __name__ == "__main__":
    unittest.main()

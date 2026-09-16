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


if __name__ == "__main__":
    unittest.main()

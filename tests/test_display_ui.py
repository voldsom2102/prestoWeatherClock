import types
import unittest

from display_ui import ClockFace


class FakeDisplay:
    """Minimal PicoGraphics-like stub sufficient to exercise ClockFace."""

    def __init__(self, width=240, height=240):
        self._bounds = (width, height)
        self.texts = []
        self.pens_created = 0

    def get_bounds(self):
        return self._bounds

    def create_pen(self, r, g, b):
        self.pens_created += 1
        return (r, g, b)

    def set_pen(self, pen):
        pass

    def clear(self):
        pass

    def measure_text(self, text, scale):
        # A stand-in for the real 8px-wide bitmap font metric.
        return len(text) * 8 * scale

    def text(self, text, x, y, wrap, scale):
        self.texts.append((text, x, y, wrap, scale))

    def circle(self, *args):
        pass

    def rectangle(self, *args):
        pass

    def line(self, *args):
        pass


def _config(**overrides):
    base = {
        "USE_24_HOUR_CLOCK": True,
        "SHOW_SECONDS": False,
        "UNITS": "metric",
    }
    base.update(overrides)
    return types.SimpleNamespace(**base)


NOW = (2026, 9, 16, 7, 30, 0, 2, 259)  # Wed 16 Sep 2026, 07:30:00


class ClockFaceDrawTests(unittest.TestCase):
    def test_draw_with_no_weather_yet_shows_loading(self):
        display = FakeDisplay()
        face = ClockFace(display, _config())

        face.draw(NOW, weather=None, weather_error=None)

        rendered = [t[0] for t in display.texts]
        self.assertIn("07:30", rendered)
        self.assertIn("Wednesday, September 16", rendered)
        self.assertIn("Loading weather...", rendered)

    def test_draw_with_weather_shows_temperature_and_description(self):
        display = FakeDisplay()
        face = ClockFace(display, _config())
        weather = {"temp": 21.4, "description": "clear sky", "icon": "01d"}

        face.draw(NOW, weather=weather, weather_error=None)

        rendered = [t[0] for t in display.texts]
        self.assertIn("21\u00b0C", rendered)
        self.assertIn("Clear sky", rendered)

    def test_draw_with_stale_weather_shows_warning(self):
        display = FakeDisplay()
        face = ClockFace(display, _config())
        weather = {"temp": 21.4, "description": "clear sky", "icon": "01d"}

        face.draw(NOW, weather=weather, weather_error="timed out")

        rendered = [t[0] for t in display.texts]
        self.assertIn("Showing last known reading", rendered)

    def test_12_hour_clock_setting_is_honoured(self):
        display = FakeDisplay()
        face = ClockFace(display, _config(USE_24_HOUR_CLOCK=False))

        face.draw(NOW, weather=None, weather_error=None)

        rendered = [t[0] for t in display.texts]
        self.assertIn("07:30 AM", rendered)

    def test_full_res_screen_uses_larger_scales(self):
        display = FakeDisplay(width=480, height=480)
        face = ClockFace(display, _config())
        self.assertGreater(face.big_scale, ClockFace(FakeDisplay(), _config()).big_scale)


if __name__ == "__main__":
    unittest.main()

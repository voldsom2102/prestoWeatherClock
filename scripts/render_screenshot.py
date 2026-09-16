"""Dev-only tool: render a PNG mockup of the Presto display for the README.

Not part of the on-device firmware - runs on a host with Pillow installed:

    python3 scripts/render_screenshot.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from display_ui import ClockFace  # noqa: E402

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


class MockDisplay:
    """Just enough of the PicoGraphics API for ClockFace/weather_icons to draw into a PIL image."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.image = Image.new("RGB", (width, height))
        self.draw = ImageDraw.Draw(self.image)
        self._pens = []
        self._pen = (0, 0, 0)
        self._fonts = {}

    def get_bounds(self):
        return self.width, self.height

    def create_pen(self, r, g, b):
        self._pens.append((r, g, b))
        return len(self._pens) - 1

    def set_pen(self, pen):
        self._pen = self._pens[pen]

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), fill=self._pen)

    def _font(self, scale):
        px = max(int(scale * 8 * 1.35), 8)
        if px not in self._fonts:
            self._fonts[px] = ImageFont.truetype(FONT_PATH, px)
        return self._fonts[px]

    def measure_text(self, text, scale):
        return int(self._font(scale).getlength(text))

    def text(self, text, x, y, wrap_width, scale):
        self.draw.text((x, y), text, font=self._font(scale), fill=self._pen)

    def circle(self, cx, cy, r):
        self.draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=self._pen)

    def rectangle(self, x, y, w, h):
        self.draw.rectangle((x, y, x + w, y + h), fill=self._pen)

    def line(self, x1, y1, x2, y2):
        self.draw.line((x1, y1, x2, y2), fill=self._pen, width=3)


def main():
    display = MockDisplay(480, 480)
    clock_face = ClockFace(display, config)

    now = (2026, 9, 16, 22, 14, 0, 2, 0)  # year, month, day, hour, minute, second, weekday, yearday
    weather = {"temp": 14.0, "description": "clear sky", "icon": "01d"}
    clock_face.draw(now, weather, weather_error=None)

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshot.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    display.image.save(out_path)
    print("Wrote {}".format(out_path))


if __name__ == "__main__":
    main()

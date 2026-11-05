"""Simple weather icons drawn with basic PicoGraphics primitives.

No image assets or extra fonts required - everything is built from
circles, rectangles and lines so it works on a freshly-flashed board.
"""

# OpenWeatherMap icon codes group into a handful of families:
# https://openweathermap.org/weather-conditions
_CLEAR = ("01",)
_FEW_CLOUDS = ("02",)
_CLOUDS = ("03", "04")
_RAIN = ("09", "10")
_THUNDER = ("11",)
_SNOW = ("13",)
_MIST = ("50",)


def _family(icon_code):
    code = (icon_code or "")[:2]
    for family in (_CLEAR, _FEW_CLOUDS, _CLOUDS, _RAIN, _THUNDER, _SNOW, _MIST):
        if code in family:
            return family
    return None


def _draw_sun(display, cx, cy, r, fg):
    display.set_pen(fg)
    display.circle(cx, cy, r)
    ray = int(r * 1.6)
    for dx, dy in ((0, -ray), (0, ray), (-ray, 0), (ray, 0)):
        display.line(cx + dx // 2, cy + dy // 2, cx + dx, cy + dy)


def _draw_cloud(display, cx, cy, r, pen):
    display.set_pen(pen)
    display.circle(cx - r // 2, cy + r // 4, int(r * 0.6))
    display.circle(cx + r // 3, cy + r // 4, int(r * 0.7))
    display.circle(cx, cy - r // 5, r)
    display.rectangle(cx - r, cy, r * 2, int(r * 0.8))


def _draw_rain(display, cx, cy, r, fg, accent):
    for i, dx in enumerate((-r // 2, 0, r // 2)):
        x = cx + dx
        y = cy + r + 2
        display.set_pen(accent)
        display.line(x, y, x - 2, y + 6)


def _draw_snow(display, cx, cy, r, fg):
    for dx in (-r // 2, 0, r // 2):
        display.set_pen(fg)
        display.circle(cx + dx, cy + r + 4, 2)


def _draw_bolt(display, cx, cy, r, accent):
    display.set_pen(accent)
    display.line(cx, cy + r - 2, cx - 4, cy + r + 6)
    display.line(cx - 4, cy + r + 6, cx + 2, cy + r + 6)
    display.line(cx + 2, cy + r + 6, cx - 2, cy + r + 14)


def _draw_mist(display, cx, cy, r, fg):
    display.set_pen(fg)
    for i, dy in enumerate((-r // 2, 0, r // 2)):
        display.rectangle(cx - r, cy + dy, r * 2, 3)


def draw(display, icon_code, cx, cy, size, fg, accent):
    """Draw a weather icon of roughly `size` radius, centred on (cx, cy)."""
    family = _family(icon_code)
    r = max(size, 6)

    if family is _CLEAR:
        _draw_sun(display, cx, cy, r, accent)
    elif family is _FEW_CLOUDS:
        _draw_sun(display, cx - r // 2, cy - r // 3, int(r * 0.7), accent)
        _draw_cloud(display, cx + r // 4, cy + r // 4, r, fg)
    elif family is _CLOUDS:
        _draw_cloud(display, cx, cy, r, fg)
    elif family is _RAIN:
        _draw_cloud(display, cx, cy, r, fg)
        _draw_rain(display, cx, cy, r, fg, accent)
    elif family is _THUNDER:
        _draw_cloud(display, cx, cy, r, fg)
        _draw_bolt(display, cx, cy, r, accent)
    elif family is _SNOW:
        _draw_cloud(display, cx, cy, r, fg)
        _draw_snow(display, cx, cy, r, fg)
    elif family is _MIST:
        _draw_mist(display, cx, cy, r, fg)
    else:
        # Unknown/missing icon code - draw a plain cloud rather than nothing.
        _draw_cloud(display, cx, cy, r, fg)

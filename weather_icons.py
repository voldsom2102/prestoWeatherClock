"""Simple weather icons drawn with basic PicoGraphics primitives.

No image assets or extra fonts required - everything is built from
circles, rectangles, triangles and lines so it works on a freshly-flashed
board. Two icon sets are available, chosen with ICON_SET in config.py:

* "classic" - the original monochrome-ish icons.
* "5c" - flat, filled, coloured icons in the style of the "5c" set from
  MMM-OpenWeatherForecast.
"""

import math

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


def _draw_classic(display, icon_code, cx, cy, size, fg, accent):
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


# --- "5c" icon set: flat, filled and coloured ---

_RGB = {
    "sun": (255, 205, 30),
    "moon": (238, 228, 185),
    "cloud": (246, 248, 252),
    "shade": (196, 205, 220),
    "drop": (30, 160, 225),
    "ice": (90, 195, 255),
    "bolt": (255, 214, 40),
}
_pen_cache = {"display": None, "pens": None}


def _pens(display):
    if _pen_cache["display"] is not display:
        _pen_cache["pens"] = {name: display.create_pen(*rgb) for name, rgb in _RGB.items()}
        _pen_cache["display"] = display
    return _pen_cache["pens"]


def _sun_5c(display, pens, cx, cy, r):
    display.set_pen(pens["sun"])
    display.circle(cx, cy, int(r * 0.8))
    tooth = max(int(r * 0.22), 1)
    for i in range(8):
        a = i * math.pi / 4
        display.circle(cx + int(math.cos(a) * r * 0.88), cy + int(math.sin(a) * r * 0.88), tooth)


def _moon_5c(display, pens, cx, cy, r, bg):
    display.set_pen(pens["moon"])
    display.circle(cx, cy, int(r * 0.85))
    if bg is not None:
        # Bite a circle out of the disc to leave a crescent.
        display.set_pen(bg)
        display.circle(cx + int(r * 0.45), cy - int(r * 0.35), int(r * 0.75))


def _cloud_shape_5c(display, cx, cy, r, pen):
    display.set_pen(pen)
    display.circle(cx - int(r * 0.6), cy + int(r * 0.05), int(r * 0.45))
    display.circle(cx + int(r * 0.6), cy + int(r * 0.1), int(r * 0.4))
    display.circle(cx - int(r * 0.1), cy - int(r * 0.2), int(r * 0.6))
    display.rectangle(cx - int(r * 0.6), cy + int(r * 0.1), int(r * 1.2), int(r * 0.4))


def _cloud_5c(display, pens, cx, cy, r):
    _cloud_shape_5c(display, cx, cy + max(r // 10, 1), r, pens["shade"])
    _cloud_shape_5c(display, cx, cy, r, pens["cloud"])


def _drop_5c(display, pens, x, y, w):
    display.set_pen(pens["drop"])
    display.circle(x, y, w)
    display.triangle(x, y - w * 2, x - w, y - w // 3, x + w, y - w // 3)


def _flake_5c(display, pens, x, y, w):
    display.set_pen(pens["ice"])
    for dx, dy in ((w, 0), (w // 2, w), (-w // 2, w)):
        display.line(x - dx, y - dy, x + dx, y + dy)
    display.circle(x, y, max(w // 4, 1))


def _bolt_5c(display, pens, x, y, u):
    display.set_pen(pens["bolt"])
    display.triangle(x + int(u * 0.3), y, x - int(u * 0.25), y + int(u * 0.65), x + int(u * 0.2), y + int(u * 0.65))
    display.triangle(x - int(u * 0.2), y + int(u * 0.5), x + int(u * 0.35), y + int(u * 0.5), x - int(u * 0.1), y + int(u * 1.25))


def _draw_5c(display, icon_code, cx, cy, size, bg):
    pens = _pens(display)
    family = _family(icon_code)
    night = (icon_code or "")[2:3] == "n"
    r = max(size, 6)

    def body(x, y, radius):
        if night:
            _moon_5c(display, pens, x, y, radius, bg)
        else:
            _sun_5c(display, pens, x, y, radius)

    if family is _CLEAR:
        body(cx, cy, r)
        return
    if family is _FEW_CLOUDS:
        body(cx - int(r * 0.4), cy - int(r * 0.35), int(r * 0.7))
        _cloud_5c(display, pens, cx + r // 5, cy + int(r * 0.2), int(r * 0.95))
        return

    precip = family in (_RAIN, _THUNDER, _SNOW, _MIST)
    _cloud_5c(display, pens, cx, cy - int(r * (0.3 if precip else 0.1)), r)
    w = max(r // 5, 2)
    top = cy + int(r * 0.45)
    if family is _RAIN:
        for dx in (-r // 2, 0, r // 2):
            _drop_5c(display, pens, cx + dx, top + w, w)
    elif family is _THUNDER:
        _drop_5c(display, pens, cx - int(r * 0.6), top + w, w)
        _drop_5c(display, pens, cx + int(r * 0.6), top + w, w)
        _bolt_5c(display, pens, cx, cy + int(r * 0.3), r)
    elif family is _SNOW:
        for dx in (-r // 2, 0, r // 2):
            _flake_5c(display, pens, cx + dx, top + w, w)
    elif family is _MIST:
        display.set_pen(pens["ice"])
        for i, dx in enumerate((0, r // 4, 0)):
            y = top + i * (w + 2)
            display.rectangle(cx - int(r * 0.6) + dx, y, int(r * 1.0), max(w // 2, 2))


def draw(display, icon_code, cx, cy, size, fg, accent, icon_set="classic", bg=None):
    """Draw a weather icon of roughly `size` radius, centred on (cx, cy).

    `bg` is the screen background pen; the "5c" set uses it to cut out the
    crescent moon at night. Unknown `icon_set` values use the classic icons.
    """
    if icon_set == "5c":
        _draw_5c(display, icon_code, cx, cy, size, bg)
    else:
        _draw_classic(display, icon_code, cx, cy, size, fg, accent)

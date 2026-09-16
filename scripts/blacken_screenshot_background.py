"""Dev-only tool: flatten docs/screenshot.png's background to pure black.

Keeps bright (white lettering) pixels untouched and zeroes everything below
a luminance threshold, so on-device photos get a clean black background
without disturbing the text/icon:

    python3 scripts/blacken_screenshot_background.py
"""

import os

from PIL import Image

THRESHOLD = 150
IMG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshot.png")


def main():
    img = Image.open(IMG_PATH).convert("RGB")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if (r + g + b) / 3 < THRESHOLD:
                px[x, y] = (0, 0, 0)
    img.save(IMG_PATH)
    print("Wrote {}".format(IMG_PATH))


if __name__ == "__main__":
    main()

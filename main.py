"""
Presto Weather Clock - entry point.

A nightstand digital clock with live weather from OpenWeatherMap, for the
Pimoroni Presto. Copy this whole project to your Presto (Thonny's "Upload"
or drag-and-drop both work) after setting up secrets.py - see README.md.
"""

import gc
import time

import machine
import usocket as socket
import ustruct as struct
from presto import Presto

import config
from display_ui import ClockFace
from timeutil import is_night, local_time
from weather import OpenWeatherClient, WeatherError

try:
    import secrets
except ImportError:
    secrets = None


def _check_secrets():
    if secrets is None:
        raise RuntimeError(
            "secrets.py not found. Copy secrets.example.py to secrets.py and "
            "fill in your Wi-Fi and OpenWeatherMap details."
        )
    missing = [
        name
        for name in ("WIFI_SSID", "WIFI_PASSWORD", "OPENWEATHER_API_KEY")
        if not getattr(secrets, name, None)
    ]
    if missing:
        raise RuntimeError("secrets.py is missing: " + ", ".join(missing))


_check_secrets()

presto = Presto(full_res=config.FULL_RES, ambient_light=config.AMBIENT_LIGHT)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()

_WHITE = display.create_pen(235, 240, 250)
_BLACK = display.create_pen(8, 10, 20)
_RED = display.create_pen(230, 90, 70)


def show_message(text, pen=_WHITE):
    """A tiny full-screen status message, used only during start-up."""
    display.set_pen(_BLACK)
    display.clear()
    display.set_pen(pen)
    display.text(text, 10, 10, WIDTH - 20, 2)
    presto.update()


# Fixed IPs for time.cloudflare.com and time.google.com: a DNS lookup (as
# ntptime.settime() does) has no timeout on MicroPython and can hang forever
# if the router doesn't answer, so we skip DNS entirely.
_NTP_SERVERS = ("162.159.200.1", "216.239.35.0")
_NTP_DELTA = 3155673600  # seconds between the NTP epoch (1900) and the RP2040's (2000)


def sync_time_from_ntp(timeout_s=2):
    """Set the RTC from NTP, bounded by our own deadline so it can never hang boot.

    Uses a non-blocking socket and a manual ticks_ms() deadline rather than
    socket.settimeout(), since some MicroPython network drivers don't honour
    a UDP recv timeout and will block forever if a reply never arrives.
    """
    query = bytearray(48)
    query[0] = 0x1B
    last_err = OSError("no NTP servers reachable")
    for host in _NTP_SERVERS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        msg = None
        last_shown = None
        try:
            sock.sendto(query, (host, 123))
            deadline = time.ticks_add(time.ticks_ms(), int(timeout_s * 1000))
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                remaining_s = time.ticks_diff(deadline, time.ticks_ms()) // 1000 + 1
                if remaining_s != last_shown:
                    show_message("Syncing time...\nTrying {}\nTimeout in {}s".format(host, remaining_s))
                    last_shown = remaining_s
                try:
                    msg = sock.recv(48)
                    break
                except OSError:
                    time.sleep_ms(50)
        except OSError as err:
            last_err = err
        finally:
            sock.close()
        if not msg:
            last_err = OSError("timed out waiting for {}".format(host))
            continue
        secs = struct.unpack("!I", msg[40:44])[0] - _NTP_DELTA
        tm = time.gmtime(secs)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        return
    raise last_err


show_message("Connecting to Wi-Fi...")
try:
    presto.connect()
except (ValueError, ImportError, OSError) as err:
    show_message("Wi-Fi connect failed:\n{}\n\nCheck secrets.py and restart.".format(err), _RED)
    while True:
        time.sleep(1)

show_message("Syncing time...")
try:
    sync_time_from_ntp()
except OSError as err:
    show_message("NTP sync failed:\n{}\n\nContinuing with the onboard clock.".format(err), _RED)
    time.sleep(2)

weather_client = OpenWeatherClient(
    api_key=secrets.OPENWEATHER_API_KEY,
    location=config.LOCATION,
    units=config.UNITS,
)

clock_face = ClockFace(display, config)

UTC_OFFSET = getattr(secrets, "UTC_OFFSET", 0)
WEATHER_INTERVAL_S = max(config.WEATHER_UPDATE_INTERVAL_MINUTES, 1) * 60

current_weather = None
weather_error = None
last_weather_fetch = 0
last_backlight = None


def refresh_weather():
    """Fetch new weather, but never let a network hiccup take the clock down."""
    global current_weather, weather_error, last_weather_fetch
    try:
        current_weather = weather_client.fetch()
        weather_error = None
    except WeatherError as err:
        weather_error = str(err)
    except Exception as err:  # noqa: BLE001 - keep the clock alive no matter what
        weather_error = "Unexpected error: {}".format(err)
    last_weather_fetch = time.time()


refresh_weather()

touch = presto.touch

while True:
    touch.poll()

    now = local_time(time.time(), UTC_OFFSET, time)
    hour = now[3]

    due_for_refresh = (time.time() - last_weather_fetch) >= WEATHER_INTERVAL_S
    if touch.state or due_for_refresh:
        refresh_weather()

    if config.NIGHT_DIMMING_ENABLED and is_night(hour, config.NIGHT_START_HOUR, config.NIGHT_END_HOUR):
        brightness = config.NIGHT_BRIGHTNESS
    else:
        brightness = config.DAY_BRIGHTNESS

    if brightness != last_backlight:
        presto.set_backlight(brightness)
        last_backlight = brightness

    clock_face.draw(now, current_weather, weather_error)
    presto.update()
    gc.collect()

    time.sleep(1 if config.SHOW_SECONDS else 5)

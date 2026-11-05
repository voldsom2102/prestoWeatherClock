If you like my work, consider buying me a coffee.

<a href="https://ko-fi.com/ajmartin_dev"><img height="36" src="https://storage.ko-fi.com/cdn/kofi6.png?v=6" alt="Buy Me a Coffee at ko-fi.com" /></a>

# Presto Weather Clock

A nightstand digital clock and weather display for the
[Pimoroni Presto](https://shop.pimoroni.com/products/presto) - a
RP2350-powered, 4" touchscreen display. It shows the current time and
live conditions from [OpenWeatherMap](https://openweathermap.org/), and
automatically dims itself at night so it isn't dazzling on a bedside
table.

![Screenshot of the clock face showing the time, date, temperature and a sun icon](docs/screenshot.png)

## Features

- Large, centred digital clock (12h or 24h, with or without seconds).
- Current weather from OpenWeatherMap: temperature, condition and a
  simple hand-drawn icon (sun, cloud, rain, snow, storm, mist) - no
  image assets or extra fonts required.
- Automatically uses the configured weather location's timezone offset,
  including daylight-saving changes.
- Automatic nightstand dimming on a configurable schedule.
- Tap the screen at any time to force an immediate weather refresh.
- Resilient by design: if Wi-Fi, NTP or the weather API misbehave, the
  clock keeps running and shows the last known-good weather instead of
  crashing or freezing.

## Hardware

- [Pimoroni Presto](https://shop.pimoroni.com/products/presto)
- The latest [Presto MicroPython firmware](https://github.com/pimoroni/presto/releases/latest)
  flashed to the board (see [Getting Started with Presto](https://learn.pimoroni.com/article/getting-started-with-presto))

## Project layout

| File | Purpose |
| --- | --- |
| `main.py` | Entry point: connects to Wi-Fi, syncs time, and runs the main draw loop. |
| `config.py` | Non-secret settings (location, units, dimming schedule, etc). Safe to commit. |
| `secrets.example.py` | Template for `secrets.py` - Wi-Fi credentials, API key, fallback UTC offset. |
| `timeutil.py` | Time/date formatting and the day/night window calculation. |
| `weather.py` | Minimal OpenWeatherMap "current weather" client. |
| `weather_icons.py` | Draws weather icons from basic shapes (no image files needed). |
| `display_ui.py` | Lays out and draws the clock + weather screen. |
| `ota_update.py` | Optional over-the-air updater (see [OTA updates](#ota-updates-optional)). |
| `ota_config.example.py` | Template for `ota_config.py` - update server URL and check interval. |
| `version.example.json` | Template for the device's `version.json` (installed version). |
| `updates/` | Example of the files you host on your update server. |
| `scripts/generate_ota_manifest.py` | Dev-machine tool that builds `updates/` with checksums. |
| `tests/` | Host-run unit tests (see [Development](#development)) for the pure-Python logic. |

## Setup

1. **Get an OpenWeatherMap API key.** Sign up for a free account at
   <https://openweathermap.org/api> and copy your API key.

2. **Copy the secrets template** and fill in your details:

   ```sh
   cp secrets.example.py secrets.py
   ```

   ```python
   WIFI_SSID = "your-network-name"
   WIFI_PASSWORD = "your-network-password"
   OPENWEATHER_API_KEY = "your-openweathermap-api-key"
   UTC_OFFSET = 0  # fallback only; e.g. -5 for New York, 1 for Paris
   ```

   `secrets.py` is listed in `.gitignore` and is never committed.

3. **Edit `config.py`** to taste - at minimum set your `LOCATION`:

   ```python
   LOCATION = {"city": "London,GB"}
   # or, for better accuracy in small towns:
   # LOCATION = {"lat": 51.5072, "lon": -0.1276}
   ```

   See the comments in `config.py` for the full set of options
   (12h/24h clock, seconds, units, update interval, resolution, ambient
   LEDs, and the night-dimming schedule).

4. **Copy the project to your Presto.** With the board connected and
   running the Presto firmware, use [Thonny](https://thonny.org/) (or
   `mpremote`/`rshell`) to upload every `.py` file in this repository
   to the root of the board's filesystem, so it ends up looking like:

   ```
   /main.py
   /config.py
   /secrets.py
   /timeutil.py
   /weather.py
   /weather_icons.py
   /display_ui.py
   ```

5. **Reset the board.** Presto automatically runs `main.py` on boot, so
   it will connect to Wi-Fi, sync the time and start showing the clock.

## OTA updates (optional)

The clock can update itself from a web server you control, so you don't
need to reconnect it to a computer. It is off unless you create
`ota_config.py`.

**One-time device setup**

1. `cp ota_config.example.py ota_config.py` and set `OTA_UPDATE_URL`
   (use `https`) and `OTA_CHECK_INTERVAL_HOURS`.
2. Upload `ota_config.py`, `ota_update.py` and `version.json` (copy of
   `version.example.json`) to the board along with the other files.

**Publishing an update**

```sh
python scripts/generate_ota_manifest.py 1.0.1 https://your-server.example.com/presto-weather-clock/
```

This copies the updatable files into `updates/` and writes
`updates/version.json` with each file's URL and SHA-256 (see
`updates/` for the layout). Upload everything in `updates/` to
that URL. In other words, the contents of the local `updates/` folder go
in the `presto-weather-clock/` folder on your server, so that
`https://your-server.example.com/presto-weather-clock/version.json` works,
and `OTA_UPDATE_URL` in `ota_config.py` is that same base URL. On its next check (at most `OTA_CHECK_INTERVAL_HOURS` later) the
clock downloads the files, verifies every checksum, swaps them in and
restarts. The new version must be higher than the one in the device's
`version.json`.

If you don't have a web server, the update files will also be hosted at
<https://www.ajmartin.dev/presto-weather-clock>. Set `OTA_UPDATE_URL` in
`ota_config.py` to `https://www.ajmartin.dev/presto-weather-clock/` to use
that hosted copy. (Maintainers: when `updates/version.json` changes on
`main`, the `sync-ota-to-site` GitHub Action copies `updates/` to
`src/public/presto-weather-clock/` in the `astro-personal-site` repo. It
needs a `SITE_REPO_TOKEN` secret: a personal access token with write access
to that repo's contents.)

**Safety**

- Files are downloaded and verified before anything is replaced; if any
  download or checksum fails, nothing changes. If the swap itself fails,
  the previous files are restored.
- Only `main.py`, `timeutil.py`, `weather.py`, `weather_icons.py`,
  `display_ui.py` and `ota_update.py` can be updated. `config.py`,
  `secrets.py` and `ota_config.py` are never touched.
- Checksums detect corruption, not tampering: anyone who controls your
  server (or intercepts plain `http`) can ship code to the clock. Use
  `https` and a server only you can write to.
- A failed check or update shows a message and the clock keeps running.

## Configuration reference

### `secrets.py` (not committed)

| Setting | Description |
| --- | --- |
| `WIFI_SSID` / `WIFI_PASSWORD` | Your wireless network credentials. |
| `OPENWEATHER_API_KEY` | Your free OpenWeatherMap API key. |
| `UTC_OFFSET` | Fallback hours offset from UTC, used only if the weather response has no timezone offset. |

### `config.py` (committed, safe to share)

| Setting | Default | Description |
| --- | --- | --- |
| `LOCATION` | `{"city": "London,GB"}` | City name (`"City,CC"`) or `{"lat":.., "lon":..}` coordinates. The clock follows this location's timezone, so set it to the place whose local time you want. |
| `UNITS` | `"metric"` | `"metric"` (°C) or `"imperial"` (°F). |
| `USE_24_HOUR_CLOCK` | `True` | 24-hour vs 12-hour clock display. |
| `SHOW_SECONDS` | `False` | Show `HH:MM:SS` instead of `HH:MM`. |
| `WEATHER_UPDATE_INTERVAL_MINUTES` | `10` | How often to poll OpenWeatherMap. |
| `FULL_RES` | `False` | `True` for crisp 480x480 rendering (slower to redraw). |
| `AMBIENT_LIGHT` | `True` | Mirror the screen colours on Presto's onboard RGB LEDs. |
| `NIGHT_DIMMING_ENABLED` | `True` | Automatically dim the backlight overnight. |
| `NIGHT_START_HOUR` / `NIGHT_END_HOUR` | `22` / `7` | Local-time (24h) window during which the screen is dimmed. |
| `DAY_BRIGHTNESS` / `NIGHT_BRIGHTNESS` | `1.0` / `0.05` | Backlight levels (`0.0`-`1.0`) outside/inside the night window. |

> **Note on `AMBIENT_LIGHT` vs. night dimming:** these are two independent
> hardware features. `NIGHT_DIMMING_ENABLED` only changes the LCD panel's
> backlight (via `presto.set_backlight()`); it never touches the onboard
> RGB LEDs. When `AMBIENT_LIGHT` is `True`, those LEDs are driven entirely
> by Presto's own firmware, which mirrors the colours already on screen -
> so they can appear to dim or change on their own, independently of the
> backlight brightness setting above. Also note that Presto's backlight PWM
> curve is very non-linear: only `1.0` is true full brightness, and most
> other values collapse onto a narrow, barely-distinguishable low range, so
> `NIGHT_BRIGHTNESS` needs to be quite low (e.g. `0.05`) to look visibly
> dimmer than daytime.

## How it works

- `main.py` connects to Wi-Fi using Presto's built-in `secrets.py`
  convention, syncs the clock over NTP, then loops forever: it polls
  touch, refreshes the weather on a timer (or immediately on tap),
  uses the weather location's current UTC offset for the displayed local
  time (including DST), adjusts the backlight for day/night, and redraws
  the screen. `UTC_OFFSET` is the fallback if the response omits it.
- Weather fetch failures (bad Wi-Fi, API downtime, quota limits, etc.)
  are caught and remembered as a message rather than raised, so the
  clock keeps ticking and simply shows the last successful reading
  with a small "showing last known reading" note.
- Weather icons are drawn from circles, rectangles and lines rather
  than bundled image files, so there's nothing extra to upload or that
  can go missing from the filesystem.

## Development

The hardware-specific modules (`presto`, `ntptime`, the Presto build of
`requests`) only exist on-device, but the pure logic - time formatting,
the day/night window, the OpenWeatherMap client and the screen layout -
is written so it can also run under regular CPython and be unit
tested on your computer:

```sh
python -m unittest discover -s tests -v
```

Tests use `unittest.mock` to stand in for the network, and small fake
"display" objects to stand in for PicoGraphics, so no hardware or
network access is required.

## License

MIT - see [LICENSE](LICENSE).

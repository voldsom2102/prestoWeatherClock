"""
Non-secret configuration for Presto Weather Clock.

Everything in this file is safe to commit to version control. Wi-Fi
credentials, your OpenWeatherMap API key and your UTC offset live in
secrets.py instead (see secrets.example.py) so they never end up in git
history.
"""

# --- Location ---
# Option A: search by city name, optionally with an ISO 3166 country code.
LOCATION = {"city": "London,GB"}
# Option B: search by coordinates instead - more accurate for small towns.
# Comment out LOCATION above and uncomment this:
# LOCATION = {"lat": 51.5072, "lon": -0.1276}

# --- Units ---
# "metric" for Celsius + m/s, "imperial" for Fahrenheit + mph.
UNITS = "metric"

# --- Clock ---
USE_24_HOUR_CLOCK = True
SHOW_SECONDS = False

# --- Weather ---
# How often to poll the OpenWeatherMap API, in minutes. OpenWeatherMap's
# free tier only refreshes its data roughly every 10 minutes, so polling
# more often than that just spends your API quota for no benefit.
WEATHER_UPDATE_INTERVAL_MINUTES = 10

# --- Display ---
# True = crisp 480x480 rendering (slower to redraw).
# False = quarter resolution, quick and plenty for a nightstand clock.
FULL_RES = False
# Let Presto's onboard RGB LEDs mirror the screen's colours.
AMBIENT_LIGHT = True

# --- Nightstand dimming ---
# Automatically dim the backlight overnight so it isn't dazzling in a
# dark bedroom, then brighten it again in the morning.
NIGHT_DIMMING_ENABLED = True
NIGHT_START_HOUR = 22  # 10pm, local time, 24-hour clock
NIGHT_END_HOUR = 7  # 7am
DAY_BRIGHTNESS = 1.0  # 0.0 - 1.0
NIGHT_BRIGHTNESS = 0.15  # 0.0 - 1.0

# Copy this file to secrets.py and fill in your own details.
# secrets.py is listed in .gitignore and is never committed.

# --- Wi-Fi ---
WIFI_SSID = "your-network-name"
WIFI_PASSWORD = "your-network-password"

# --- OpenWeatherMap ---
# Free API key: https://openweathermap.org/api
OPENWEATHER_API_KEY = "your-openweathermap-api-key"

# --- Time zone ---
# Hours offset from UTC, e.g. -5 for New York, 1 for Paris.
# MicroPython has no timezone database so there's no automatic daylight
# saving - update this by hand when your local clocks change.
UTC_OFFSET = 0

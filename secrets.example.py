# Copy this file to secrets.py and fill in your own details.
# secrets.py is listed in .gitignore and is never committed.

# --- Wi-Fi ---
WIFI_SSID = "your-network-name"
WIFI_PASSWORD = "your-network-password"

# --- OpenWeatherMap ---
# Free API key: https://openweathermap.org/api
OPENWEATHER_API_KEY = "your-openweathermap-api-key"

# --- Time zone ---
# Fallback hours offset from UTC, e.g. -5 for New York, 1 for Paris.
# The clock normally gets the current offset (including DST) from the
# configured OpenWeatherMap location; this is used if that is unavailable.
UTC_OFFSET = 0

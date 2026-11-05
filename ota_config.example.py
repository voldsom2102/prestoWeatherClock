# Copy this file to ota_config.py and fill in your own details.
# ota_config.py is listed in .gitignore and is never committed.

# --- OTA updates ---
# Set to False to never check for updates.
OTA_ENABLED = True

# Base URL that hosts version.json and the .py files produced by
# generate_ota_manifest.py (see updates/ for the layout). Use https.
OTA_UPDATE_URL = "https://your-server.example.com/presto-weather-clock/"

# How often to check for updates, in hours.
OTA_CHECK_INTERVAL_HOURS = 24

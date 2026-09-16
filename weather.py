"""A tiny OpenWeatherMap "current weather" client.

Uses the `requests` module that ships with Presto's MicroPython firmware
(an alias for `urequests`), so this only runs on-device - it isn't meant
to be imported under CPython.
"""

import requests

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherError(Exception):
    """Raised when the OpenWeatherMap request fails or returns bad data."""


class OpenWeatherClient:
    def __init__(self, api_key, location, units="metric"):
        if not api_key:
            raise ValueError("OpenWeatherMap API key is required")
        if "city" not in location and ("lat" not in location or "lon" not in location):
            raise ValueError("location must set either 'city' or both 'lat' and 'lon'")

        self.api_key = api_key
        self.location = location
        self.units = units

    def _url(self):
        params = "appid={}&units={}".format(self.api_key, self.units)
        if "lat" in self.location and "lon" in self.location:
            params += "&lat={}&lon={}".format(self.location["lat"], self.location["lon"])
        else:
            params += "&q={}".format(self.location["city"])
        return "{}?{}".format(BASE_URL, params)

    def fetch(self):
        """Fetch current conditions and return a plain dict, or raise WeatherError."""
        response = None
        try:
            response = requests.get(self._url())
            if response.status_code != 200:
                raise WeatherError(
                    "OpenWeatherMap returned HTTP {}".format(response.status_code)
                )
            data = response.json()
        except WeatherError:
            raise
        except Exception as err:  # noqa: BLE001 - network/JSON errors vary by firmware
            raise WeatherError("Could not reach OpenWeatherMap: {}".format(err))
        finally:
            if response is not None:
                response.close()

        try:
            weather = data["weather"][0]
            main = data["main"]
        except (KeyError, IndexError) as err:
            raise WeatherError("Unexpected OpenWeatherMap response: {}".format(err))

        wind = data.get("wind", {})
        sys_info = data.get("sys", {})

        return {
            "temp": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "temp_min": main.get("temp_min"),
            "temp_max": main.get("temp_max"),
            "humidity": main.get("humidity"),
            "condition": weather.get("main"),
            "description": weather.get("description"),
            "icon": weather.get("icon"),
            "wind_speed": wind.get("speed"),
            "location_name": data.get("name"),
            "sunrise": sys_info.get("sunrise"),
            "sunset": sys_info.get("sunset"),
        }

import unittest
from unittest.mock import MagicMock, patch

from weather import OpenWeatherClient, WeatherError

SAMPLE_RESPONSE = {
    "weather": [{"main": "Clouds", "description": "scattered clouds", "icon": "03d"}],
    "main": {
        "temp": 18.5,
        "feels_like": 17.9,
        "temp_min": 16.0,
        "temp_max": 20.0,
        "humidity": 62,
    },
    "wind": {"speed": 3.6},
    "name": "London",
    "sys": {"sunrise": 1_700_000_000, "sunset": 1_700_040_000},
}


def _mock_response(json_data, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    return response


class ClientConstructionTests(unittest.TestCase):
    def test_requires_api_key(self):
        with self.assertRaises(ValueError):
            OpenWeatherClient(api_key="", location={"city": "London"})

    def test_requires_city_or_coordinates(self):
        with self.assertRaises(ValueError):
            OpenWeatherClient(api_key="key", location={})

    def test_accepts_coordinates(self):
        client = OpenWeatherClient(api_key="key", location={"lat": 1, "lon": 2})
        self.assertIn("lat=1", client._url())
        self.assertIn("lon=2", client._url())

    def test_accepts_city(self):
        client = OpenWeatherClient(api_key="key", location={"city": "Paris,FR"})
        self.assertIn("q=Paris,FR", client._url())


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.client = OpenWeatherClient(api_key="key", location={"city": "London,GB"}, units="metric")

    @patch("weather.requests")
    def test_fetch_parses_known_fields(self, mock_requests):
        mock_requests.get.return_value = _mock_response(SAMPLE_RESPONSE)

        result = self.client.fetch()

        self.assertEqual(result["temp"], 18.5)
        self.assertEqual(result["condition"], "Clouds")
        self.assertEqual(result["description"], "scattered clouds")
        self.assertEqual(result["icon"], "03d")
        self.assertEqual(result["humidity"], 62)
        self.assertEqual(result["location_name"], "London")

    @patch("weather.requests")
    def test_fetch_closes_the_response(self, mock_requests):
        response = _mock_response(SAMPLE_RESPONSE)
        mock_requests.get.return_value = response

        self.client.fetch()

        response.close.assert_called_once()

    @patch("weather.requests")
    def test_non_200_status_raises_weather_error(self, mock_requests):
        mock_requests.get.return_value = _mock_response({}, status_code=401)

        with self.assertRaises(WeatherError):
            self.client.fetch()

    @patch("weather.requests")
    def test_malformed_payload_raises_weather_error(self, mock_requests):
        mock_requests.get.return_value = _mock_response({"unexpected": True})

        with self.assertRaises(WeatherError):
            self.client.fetch()

    @patch("weather.requests")
    def test_network_failure_raises_weather_error(self, mock_requests):
        mock_requests.get.side_effect = OSError("no route to host")

        with self.assertRaises(WeatherError):
            self.client.fetch()


if __name__ == "__main__":
    unittest.main()

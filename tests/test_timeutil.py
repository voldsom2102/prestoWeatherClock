import time
import unittest

from timeutil import format_date, format_time, is_night, local_time


class FormatTimeTests(unittest.TestCase):
    def test_24_hour(self):
        self.assertEqual(format_time(13, 5, 9, True, False), "13:05")

    def test_24_hour_with_seconds(self):
        self.assertEqual(format_time(13, 5, 9, True, True), "13:05:09")

    def test_12_hour_midnight(self):
        self.assertEqual(format_time(0, 5, 0, False, False), "12:05 AM")

    def test_12_hour_afternoon(self):
        self.assertEqual(format_time(13, 5, 0, False, False), "01:05 PM")

    def test_12_hour_noon(self):
        self.assertEqual(format_time(12, 0, 0, False, False), "12:00 PM")


class FormatDateTests(unittest.TestCase):
    def test_weekday_is_derived_from_calendar_date(self):
        self.assertEqual(format_date(2026, 9, 16), "Wednesday, September 16")
        self.assertEqual(format_date(2026, 10, 16), "Friday, October 16")


class IsNightTests(unittest.TestCase):
    def test_window_wraps_past_midnight(self):
        self.assertTrue(is_night(23, 22, 7))
        self.assertTrue(is_night(2, 22, 7))
        self.assertTrue(is_night(6, 22, 7))
        self.assertFalse(is_night(7, 22, 7))
        self.assertFalse(is_night(12, 22, 7))

    def test_window_within_same_day(self):
        self.assertTrue(is_night(13, 12, 14))
        self.assertFalse(is_night(11, 12, 14))
        self.assertFalse(is_night(15, 12, 14))

    def test_disabled_when_start_equals_end(self):
        self.assertFalse(is_night(0, 10, 10))
        self.assertFalse(is_night(10, 10, 10))


class LocalTimeTests(unittest.TestCase):
    def test_offset_is_applied_on_top_of_utc(self):
        epoch = 0
        result = local_time(epoch, 1, time)
        expected = time.gmtime(3600)
        self.assertEqual(result, expected)

    def test_zero_offset_matches_gmtime(self):
        epoch = 1_700_000_000
        self.assertEqual(local_time(epoch, 0, time), time.gmtime(epoch))


if __name__ == "__main__":
    unittest.main()

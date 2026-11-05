"""Time formatting and helpers shared by the clock display.

Kept dependency-free (no external date libraries exist in MicroPython)
so it works the same on-device and in the CPython unit tests.
"""

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def local_time(now_seconds, utc_offset_hours, time_module, timezone_offset_seconds=None):
    """Return a UTC time tuple shifted by the location's UTC offset.

    MicroPython has no timezone database - `time.localtime()` on every
    port except Unix is identical to `time.gmtime()` and always reflects
    UTC. We therefore start from `gmtime()` and apply the offset ourselves.
    Prefer the location's current offset in seconds when available, falling
    back to the user's manual offset in hours.

    `time_module` is passed in (rather than imported) so this can be unit
    tested against CPython's `time` module as well as MicroPython's.
    """
    if timezone_offset_seconds is None:
        timezone_offset_seconds = int(utc_offset_hours * 3600)
    return time_module.gmtime(now_seconds + timezone_offset_seconds)


def format_time(hour, minute, second, use_24_hour, show_seconds):
    if use_24_hour:
        display_hour = hour
        suffix = ""
    else:
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        suffix = " AM" if hour < 12 else " PM"

    if show_seconds:
        return "{:02d}:{:02d}:{:02d}{}".format(display_hour, minute, second, suffix)
    return "{:02d}:{:02d}{}".format(display_hour, minute, suffix)


def format_date(year, month, day):
    days_before_year = (
        365 * (year - 1)
        + (year - 1) // 4
        - (year - 1) // 100
        + (year - 1) // 400
    )
    days_before_month = sum(
        (31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
         31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[:month - 1]
    )
    weekday = (days_before_year + days_before_month + day - 1) % 7
    return "{}, {} {}".format(WEEKDAYS[weekday], MONTHS[month - 1], day)


def is_night(hour, night_start_hour, night_end_hour):
    """Whether `hour` falls within a night window that may wrap past midnight."""
    if night_start_hour == night_end_hour:
        return False
    if night_start_hour < night_end_hour:
        return night_start_hour <= hour < night_end_hour
    return hour >= night_start_hour or hour < night_end_hour
